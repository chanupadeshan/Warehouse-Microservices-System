from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict

ContractStatus = Literal["Active", "Inactive"]


class SupplierBase(BaseModel):
    supplier_name: str = Field(..., min_length=1, max_length=100)
    company_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(..., min_length=1, max_length=30)
    address: str = Field(..., min_length=1, max_length=255)
    contract_status: ContractStatus = "Active"


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = Field(None, min_length=1, max_length=100)
    company_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=1, max_length=30)
    address: Optional[str] = Field(None, min_length=1, max_length=255)
    contract_status: Optional[ContractStatus] = None


class SupplierOut(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime