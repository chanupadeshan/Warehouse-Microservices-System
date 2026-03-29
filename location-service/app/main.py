from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, status as http_status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import StorageLocation

app = FastAPI(
    title="Location Service",
    version="1.0.0",
    description="Manage zones and bins in PostgreSQL.",
)


class LocationBase(BaseModel):
    zone_code: str = Field(..., max_length=32)
    bin_code: str = Field(..., max_length=32)
    capacity: int = Field(..., ge=0)
    status: str = Field(default="Empty", max_length=32)
    notes: str | None = Field(default=None, max_length=255)


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    zone_code: str | None = Field(default=None, max_length=32)
    bin_code: str | None = Field(default=None, max_length=32)
    capacity: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=255)


class LocationRead(LocationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LocationReservationRequest(BaseModel):
    zone_code: str | None = Field(default=None, max_length=32)
    capacity_required: int = Field(default=0, ge=0)
    notes: str | None = Field(default=None, max_length=255)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "location-service", "database": "PostgreSQL", "resource": "/locations"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "location-service"}


def get_location_or_404(db: Session, location_id: int) -> StorageLocation:
    location = db.query(StorageLocation).filter(StorageLocation.id == location_id).first()
    if location is None:
        raise HTTPException(status_code=404, detail="Storage location not found.")
    return location


def commit_with_conflict_handling(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


@app.post("/locations", response_model=LocationRead, status_code=http_status.HTTP_201_CREATED)
def create_location(payload: LocationCreate, db: Session = Depends(get_db)) -> StorageLocation:
    location = StorageLocation(**payload.model_dump())
    db.add(location)
    commit_with_conflict_handling(db, "Bin code already exists.")
    db.refresh(location)
    return location


@app.get("/locations", response_model=list[LocationRead])
def list_locations(
    status: str | None = None,
    zone_code: str | None = None,
    db: Session = Depends(get_db),
) -> list[StorageLocation]:
    query = db.query(StorageLocation)
    if status:
        query = query.filter(StorageLocation.status == status)
    if zone_code:
        query = query.filter(StorageLocation.zone_code == zone_code)
    return query.order_by(StorageLocation.id).all()


@app.get("/locations/{location_id}", response_model=LocationRead)
def get_location(location_id: int, db: Session = Depends(get_db)) -> StorageLocation:
    return get_location_or_404(db, location_id)


@app.post("/locations/reserve", response_model=LocationRead)
def reserve_location(
    payload: LocationReservationRequest,
    db: Session = Depends(get_db),
) -> StorageLocation:
    query = db.query(StorageLocation).filter(StorageLocation.status == "Empty")
    if payload.zone_code:
        query = query.filter(StorageLocation.zone_code == payload.zone_code)
    if payload.capacity_required:
        query = query.filter(StorageLocation.capacity >= payload.capacity_required)

    location = query.order_by(StorageLocation.id).with_for_update(skip_locked=True).first()
    if location is None:
        raise HTTPException(status_code=409, detail="No suitable storage location available.")

    location.status = "Reserved"
    location.notes = payload.notes
    db.commit()
    db.refresh(location)
    return location


@app.put("/locations/{location_id}", response_model=LocationRead)
def update_location(
    location_id: int,
    payload: LocationUpdate,
    db: Session = Depends(get_db),
) -> StorageLocation:
    location = get_location_or_404(db, location_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(location, field, value)
    commit_with_conflict_handling(db, "Bin code already exists.")
    db.refresh(location)
    return location


@app.post("/locations/{location_id}/release", response_model=LocationRead)
def release_location(location_id: int, db: Session = Depends(get_db)) -> StorageLocation:
    location = get_location_or_404(db, location_id)
    location.status = "Empty"
    location.notes = None
    db.commit()
    db.refresh(location)
    return location


@app.delete("/locations/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db)) -> dict[str, int]:
    location = get_location_or_404(db, location_id)
    db.delete(location)
    db.commit()
    return {"deleted_id": location_id}
