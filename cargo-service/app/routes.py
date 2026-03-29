from fastapi import APIRouter, Depends, status as http_status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CargoShipment
from app.repository import commit_with_conflict_handling, get_cargo_or_404
from app.schemas import CargoCreate, CargoIntakeRequest, CargoRead, CargoUpdate
from app.workflow import run_shipment_intake_workflow

router = APIRouter()


@router.get("/")
def root() -> dict[str, str]:
    return {"service": "cargo-service", "database": "PostgreSQL", "resource": "/cargo"}


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "cargo-service"}


@router.post("/cargo", response_model=CargoRead, status_code=http_status.HTTP_201_CREATED)
def create_cargo(payload: CargoCreate, db: Session = Depends(get_db)) -> CargoShipment:
    cargo = CargoShipment(**payload.model_dump())
    db.add(cargo)
    commit_with_conflict_handling(db, "Cargo manifest number already exists.")
    db.refresh(cargo)
    return cargo


@router.post("/cargo/intake", status_code=http_status.HTTP_201_CREATED)
async def create_shipment_with_workflow(
    payload: CargoIntakeRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return await run_shipment_intake_workflow(payload, db)


@router.get("/cargo", response_model=list[CargoRead])
def list_cargo(status: str | None = None, db: Session = Depends(get_db)) -> list[CargoShipment]:
    query = db.query(CargoShipment)
    if status:
        query = query.filter(CargoShipment.status == status)
    return query.order_by(CargoShipment.id).all()


@router.get("/cargo/{cargo_id}", response_model=CargoRead)
def get_cargo(cargo_id: int, db: Session = Depends(get_db)) -> CargoShipment:
    return get_cargo_or_404(db, cargo_id)


@router.put("/cargo/{cargo_id}", response_model=CargoRead)
def update_cargo(
    cargo_id: int,
    payload: CargoUpdate,
    db: Session = Depends(get_db),
) -> CargoShipment:
    cargo = get_cargo_or_404(db, cargo_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cargo, field, value)
    commit_with_conflict_handling(db, "Cargo manifest number already exists.")
    db.refresh(cargo)
    return cargo


@router.delete("/cargo/{cargo_id}")
def delete_cargo(cargo_id: int, db: Session = Depends(get_db)) -> dict[str, int]:
    cargo = get_cargo_or_404(db, cargo_id)
    db.delete(cargo)
    db.commit()
    return {"deleted_id": cargo_id}

