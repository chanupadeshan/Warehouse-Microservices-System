from sqlalchemy.orm import Session

from app.models import CargoShipment
from app.repository import commit_with_conflict_handling
from app.schemas import CargoIntakeRequest


def create_pending_cargo(payload: CargoIntakeRequest, db: Session) -> CargoShipment:
    cargo = CargoShipment(
        manifest_number=payload.manifest_number,
        description=payload.description,
        status="Pending Verification",
        weight_kg=payload.weight_kg,
        workflow_state="Processing",
    )
    db.add(cargo)
    commit_with_conflict_handling(db, "Cargo manifest number already exists.")
    db.refresh(cargo)
    return cargo


def persist_cargo(
    db: Session,
    cargo: CargoShipment,
    *,
    status: str | None = None,
    workflow_state: str | None = None,
    **fields: object,
) -> None:
    if status is not None:
        cargo.status = status
    if workflow_state is not None:
        cargo.workflow_state = workflow_state
    for field, value in fields.items():
        setattr(cargo, field, value)
    db.commit()
    db.refresh(cargo)
