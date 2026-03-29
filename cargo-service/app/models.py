from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class CargoShipment(Base):
    __tablename__ = "cargo_shipments"

    id = Column(Integer, primary_key=True, index=True)
    manifest_number = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=False)
    status = Column(String(40), nullable=False, default="Arrived")
    weight_kg = Column(Float, nullable=False)
    supplier_id = Column(Integer, nullable=True)
    supplier_name = Column(String(120), nullable=True)
    shipping_line = Column(String(120), nullable=True)
    assigned_location_id = Column(Integer, nullable=True)
    assigned_bin = Column(String(64), nullable=True)
    assigned_staff_id = Column(Integer, nullable=True)
    assigned_staff_name = Column(String(120), nullable=True)
    assigned_equipment_id = Column(Integer, nullable=True)
    assigned_equipment_name = Column(String(120), nullable=True)
    workflow_state = Column(String(40), nullable=False, default="Manual")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
