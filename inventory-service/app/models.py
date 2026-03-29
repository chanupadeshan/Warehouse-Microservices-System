from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(64), unique=True, nullable=False, index=True)
    item_name = Column(String(120), nullable=False)
    description = Column(String(255), nullable=True)
    quantity = Column(Integer, nullable=False, default=0)
    unit = Column(String(32), nullable=False, default="units")
    status = Column(String(32), nullable=False, default="In Stock")
    cargo_id = Column(Integer, nullable=True)
    bin_code = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
