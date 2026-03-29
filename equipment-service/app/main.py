from datetime import date, datetime

from fastapi import Depends, FastAPI, HTTPException, status as http_status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Equipment

app = FastAPI(
    title="Equipment Service",
    version="1.0.0",
    description="Manage warehouse equipment in PostgreSQL.",
)


class EquipmentBase(BaseModel):
    asset_tag: str = Field(..., max_length=32)
    equipment_name: str = Field(..., max_length=120)
    equipment_type: str = Field(..., max_length=64)
    status: str = Field(default="Available", max_length=32)
    capacity_tons: float = Field(default=0, ge=0)
    last_maintenance_date: date | None = None


class EquipmentCreate(EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    asset_tag: str | None = Field(default=None, max_length=32)
    equipment_name: str | None = Field(default=None, max_length=120)
    equipment_type: str | None = Field(default=None, max_length=64)
    status: str | None = Field(default=None, max_length=32)
    capacity_tons: float | None = Field(default=None, ge=0)
    last_maintenance_date: date | None = None


class EquipmentRead(EquipmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EquipmentAssignmentRequest(BaseModel):
    equipment_type: str = Field(default="Forklift", max_length=64)
    required_capacity_tons: float = Field(default=0, ge=0)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "equipment-service", "database": "PostgreSQL", "resource": "/equipment"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "equipment-service"}


def get_equipment_or_404(db: Session, equipment_id: int) -> Equipment:
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if equipment is None:
        raise HTTPException(status_code=404, detail="Equipment asset not found.")
    return equipment


def commit_with_conflict_handling(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


@app.post("/equipment", response_model=EquipmentRead, status_code=http_status.HTTP_201_CREATED)
def create_equipment(payload: EquipmentCreate, db: Session = Depends(get_db)) -> Equipment:
    equipment = Equipment(**payload.model_dump())
    db.add(equipment)
    commit_with_conflict_handling(db, "Equipment asset tag already exists.")
    db.refresh(equipment)
    return equipment


@app.get("/equipment", response_model=list[EquipmentRead])
def list_equipment(
    status: str | None = None,
    equipment_type: str | None = None,
    db: Session = Depends(get_db),
) -> list[Equipment]:
    query = db.query(Equipment)
    if status:
        query = query.filter(Equipment.status == status)
    if equipment_type:
        query = query.filter(Equipment.equipment_type == equipment_type)
    return query.order_by(Equipment.id).all()


@app.get("/equipment/{equipment_id}", response_model=EquipmentRead)
def get_equipment(equipment_id: int, db: Session = Depends(get_db)) -> Equipment:
    return get_equipment_or_404(db, equipment_id)


@app.post("/equipment/assign", response_model=EquipmentRead)
def assign_equipment(
    payload: EquipmentAssignmentRequest,
    db: Session = Depends(get_db),
) -> Equipment:
    equipment = (
        db.query(Equipment)
        .filter(
            Equipment.status == "Available",
            Equipment.equipment_type == payload.equipment_type,
            Equipment.capacity_tons >= payload.required_capacity_tons,
        )
        .order_by(Equipment.id)
        .with_for_update(skip_locked=True)
        .first()
    )
    if equipment is None:
        raise HTTPException(status_code=409, detail="No available equipment found.")

    equipment.status = "Assigned"
    db.commit()
    db.refresh(equipment)
    return equipment


@app.put("/equipment/{equipment_id}", response_model=EquipmentRead)
def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    db: Session = Depends(get_db),
) -> Equipment:
    equipment = get_equipment_or_404(db, equipment_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(equipment, field, value)
    commit_with_conflict_handling(db, "Equipment asset tag already exists.")
    db.refresh(equipment)
    return equipment


@app.post("/equipment/{equipment_id}/release", response_model=EquipmentRead)
def release_equipment(equipment_id: int, db: Session = Depends(get_db)) -> Equipment:
    equipment = get_equipment_or_404(db, equipment_id)
    equipment.status = "Available"
    db.commit()
    db.refresh(equipment)
    return equipment


@app.delete("/equipment/{equipment_id}")
def delete_equipment(equipment_id: int, db: Session = Depends(get_db)) -> dict[str, int]:
    equipment = get_equipment_or_404(db, equipment_id)
    db.delete(equipment)
    db.commit()
    return {"deleted_id": equipment_id}
