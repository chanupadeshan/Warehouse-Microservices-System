from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from .database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)

    supplier_name = Column(String, nullable=False)
    company_name = Column(String, nullable=False)

    email = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)

    contract_status = Column(String, nullable=False, default="Active", index=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)