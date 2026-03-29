from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, status as http_status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Supplier

app = FastAPI(
    title="Supplier Service",
    version="1.0.0",
    description="Manage supplier and shipping line records in PostgreSQL.",
)


class SupplierBase(BaseModel):
    supplier_name: str = Field(..., max_length=120)
    shipping_line: str = Field(..., max_length=120)
    contact_name: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    contract_status: str = Field(default="Active", max_length=32)
    active: bool = True


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    supplier_name: str | None = Field(default=None, max_length=120)
    shipping_line: str | None = Field(default=None, max_length=120)
    contact_name: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    contract_status: str | None = Field(default=None, max_length=32)
    active: bool | None = None


class SupplierRead(SupplierBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupplierValidationRead(BaseModel):
    supplier_id: int
    supplier_name: str
    shipping_line: str
    valid: bool
    reason: str | None = None


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "supplier-service", "database": "PostgreSQL", "resource": "/suppliers"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "supplier-service"}


def get_supplier_or_404(db: Session, supplier_id: int) -> Supplier:
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found.")
    return supplier


def commit_with_conflict_handling(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


@app.post("/suppliers", response_model=SupplierRead, status_code=http_status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate, db: Session = Depends(get_db)) -> Supplier:
    supplier = Supplier(**payload.model_dump())
    db.add(supplier)
    commit_with_conflict_handling(db, "Supplier name already exists.")
    db.refresh(supplier)
    return supplier


@app.get("/suppliers", response_model=list[SupplierRead])
def list_suppliers(
    active: bool | None = None,
    shipping_line: str | None = None,
    db: Session = Depends(get_db),
) -> list[Supplier]:
    query = db.query(Supplier)
    if active is not None:
        query = query.filter(Supplier.active == active)
    if shipping_line:
        query = query.filter(Supplier.shipping_line == shipping_line)
    return query.order_by(Supplier.id).all()


@app.get("/suppliers/{supplier_id}", response_model=SupplierRead)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)) -> Supplier:
    return get_supplier_or_404(db, supplier_id)


@app.get("/suppliers/{supplier_id}/validate", response_model=SupplierValidationRead)
def validate_supplier(supplier_id: int, db: Session = Depends(get_db)) -> SupplierValidationRead:
    supplier = get_supplier_or_404(db, supplier_id)
    is_valid = supplier.active and supplier.contract_status.lower() == "active"
    reason = None if is_valid else "Supplier is inactive or contract is not active."
    return SupplierValidationRead(
        supplier_id=supplier.id,
        supplier_name=supplier.supplier_name,
        shipping_line=supplier.shipping_line,
        valid=is_valid,
        reason=reason,
    )


@app.put("/suppliers/{supplier_id}", response_model=SupplierRead)
def update_supplier(
    supplier_id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
) -> Supplier:
    supplier = get_supplier_or_404(db, supplier_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(supplier, field, value)
    commit_with_conflict_handling(db, "Supplier name already exists.")
    db.refresh(supplier)
    return supplier


@app.delete("/suppliers/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)) -> dict[str, int]:
    supplier = get_supplier_or_404(db, supplier_id)
    if supplier.active:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail="Supplier must be inactive before deletion.",
        )
    db.delete(supplier)
    db.commit()
    return {"deleted_id": supplier_id}
