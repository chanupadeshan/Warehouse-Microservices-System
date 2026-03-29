from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, status as http_status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import InventoryItem

app = FastAPI(
    title="Inventory Service",
    version="1.0.0",
    description="Manage warehouse stock records in PostgreSQL.",
)


class InventoryBase(BaseModel):
    sku: str = Field(..., max_length=64)
    item_name: str = Field(..., max_length=120)
    description: str | None = Field(default=None, max_length=255)
    quantity: int = Field(..., ge=0)
    unit: str = Field(default="units", max_length=32)
    status: str = Field(default="In Stock", max_length=32)
    cargo_id: int | None = None
    bin_code: str | None = Field(default=None, max_length=32)


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    sku: str | None = Field(default=None, max_length=64)
    item_name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=255)
    quantity: int | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, max_length=32)
    cargo_id: int | None = None
    bin_code: str | None = Field(default=None, max_length=32)


class InventoryRead(InventoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InventoryReceiveItem(BaseModel):
    sku: str = Field(..., max_length=64)
    item_name: str = Field(..., max_length=120)
    description: str | None = Field(default=None, max_length=255)
    quantity: int = Field(..., ge=1)
    unit: str = Field(default="units", max_length=32)


class InventoryReceiveRequest(BaseModel):
    cargo_id: int
    bin_code: str | None = Field(default=None, max_length=32)
    status: str = Field(default="In Stock", max_length=32)
    items: list[InventoryReceiveItem] = Field(..., min_length=1)


class InventoryReleaseItem(BaseModel):
    sku: str = Field(..., max_length=64)
    quantity: int = Field(..., ge=1)


class InventoryReleaseRequest(BaseModel):
    items: list[InventoryReleaseItem] = Field(..., min_length=1)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "inventory-service", "database": "PostgreSQL", "resource": "/inventory-items"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "inventory-service"}


def get_inventory_item_or_404(db: Session, item_id: int) -> InventoryItem:
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found.")
    return item


def commit_with_conflict_handling(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


@app.post(
    "/inventory-items",
    response_model=InventoryRead,
    status_code=http_status.HTTP_201_CREATED,
)
def create_inventory_item(
    payload: InventoryCreate,
    db: Session = Depends(get_db),
) -> InventoryItem:
    item = InventoryItem(**payload.model_dump())
    db.add(item)
    commit_with_conflict_handling(db, "Inventory SKU already exists.")
    db.refresh(item)
    return item


@app.get("/inventory-items", response_model=list[InventoryRead])
def list_inventory_items(
    status: str | None = None,
    cargo_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[InventoryItem]:
    query = db.query(InventoryItem)
    if status:
        query = query.filter(InventoryItem.status == status)
    if cargo_id is not None:
        query = query.filter(InventoryItem.cargo_id == cargo_id)
    return query.order_by(InventoryItem.id).all()


@app.get("/inventory-items/{item_id}", response_model=InventoryRead)
def get_inventory_item(item_id: int, db: Session = Depends(get_db)) -> InventoryItem:
    return get_inventory_item_or_404(db, item_id)


@app.post("/inventory/receive", response_model=list[InventoryRead])
@app.post("/inventory-items/receive", response_model=list[InventoryRead])
def receive_inventory(
    payload: InventoryReceiveRequest,
    db: Session = Depends(get_db),
) -> list[InventoryItem]:
    updated_items: list[InventoryItem] = []

    for received_item in payload.items:
        inventory_item = (
            db.query(InventoryItem).filter(InventoryItem.sku == received_item.sku).first()
        )
        if inventory_item is None:
            inventory_item = InventoryItem(
                sku=received_item.sku,
                item_name=received_item.item_name,
                description=received_item.description,
                quantity=received_item.quantity,
                unit=received_item.unit,
                status=payload.status,
                cargo_id=payload.cargo_id,
                bin_code=payload.bin_code,
            )
            db.add(inventory_item)
        else:
            inventory_item.item_name = received_item.item_name
            inventory_item.description = received_item.description
            inventory_item.quantity += received_item.quantity
            inventory_item.unit = received_item.unit
            inventory_item.status = payload.status
            inventory_item.cargo_id = payload.cargo_id
            inventory_item.bin_code = payload.bin_code
        updated_items.append(inventory_item)

    commit_with_conflict_handling(db, "Inventory SKU already exists.")
    for inventory_item in updated_items:
        db.refresh(inventory_item)
    return updated_items


@app.post("/inventory/release", response_model=list[InventoryRead])
@app.post("/inventory-items/release", response_model=list[InventoryRead])
def release_inventory(
    payload: InventoryReleaseRequest,
    db: Session = Depends(get_db),
) -> list[InventoryItem]:
    updated_items: list[InventoryItem] = []

    for released_item in payload.items:
        inventory_item = (
            db.query(InventoryItem).filter(InventoryItem.sku == released_item.sku).first()
        )
        if inventory_item is None:
            raise HTTPException(
                status_code=404,
                detail=f"Inventory item with SKU '{released_item.sku}' not found.",
            )
        if inventory_item.quantity < released_item.quantity:
            raise HTTPException(
                status_code=409,
                detail=f"Insufficient quantity for SKU '{released_item.sku}'.",
            )
        updated_items.append(inventory_item)

    for inventory_item, released_item in zip(updated_items, payload.items):
        inventory_item.quantity -= released_item.quantity
        if inventory_item.quantity == 0:
            inventory_item.status = "Out of Stock"

    db.commit()
    for inventory_item in updated_items:
        db.refresh(inventory_item)
    return updated_items


@app.put("/inventory-items/{item_id}", response_model=InventoryRead)
def update_inventory_item(
    item_id: int,
    payload: InventoryUpdate,
    db: Session = Depends(get_db),
) -> InventoryItem:
    item = get_inventory_item_or_404(db, item_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    commit_with_conflict_handling(db, "Inventory SKU already exists.")
    db.refresh(item)
    return item


@app.delete("/inventory-items/{item_id}")
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)) -> dict[str, int]:
    item = get_inventory_item_or_404(db, item_id)
    db.delete(item)
    db.commit()
    return {"deleted_id": item_id}
