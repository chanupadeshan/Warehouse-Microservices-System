from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(120), unique=True, nullable=False, index=True)
    shipping_line = Column(String(120), nullable=False, index=True)
    contact_name = Column(String(120), nullable=True)
    email = Column(String(120), nullable=True)
    phone = Column(String(40), nullable=True)
    contract_status = Column(String(32), nullable=False, default="Active")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
