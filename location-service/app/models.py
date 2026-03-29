from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class StorageLocation(Base):
    __tablename__ = "storage_locations"

    id = Column(Integer, primary_key=True, index=True)
    zone_code = Column(String(32), nullable=False, index=True)
    bin_code = Column(String(32), unique=True, nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    status = Column(String(32), nullable=False, default="Empty")
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
