from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import CargoShipment


def get_cargo_or_404(db: Session, cargo_id: int) -> CargoShipment:
    cargo = db.query(CargoShipment).filter(CargoShipment.id == cargo_id).first()
    if cargo is None:
        raise HTTPException(status_code=404, detail="Cargo shipment not found.")
    return cargo


def commit_with_conflict_handling(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc

