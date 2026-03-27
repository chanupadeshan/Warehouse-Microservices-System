from sqlalchemy import Column, Date, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class Equipment(Base):
    __tablename__ = "equipment_assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_tag = Column(String(32), unique=True, nullable=False, index=True)
    equipment_name = Column(String(120), nullable=False)
    equipment_type = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="Available")
    capacity_tons = Column(Float, nullable=False, default=0)
    last_maintenance_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
