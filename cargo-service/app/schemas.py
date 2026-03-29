from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CargoBase(BaseModel):
    manifest_number: str = Field(..., max_length=64)
    description: str = Field(..., max_length=255)
    status: str = Field(default="Arrived", max_length=40)
    weight_kg: float = Field(..., ge=0)
    supplier_id: int | None = None
    supplier_name: str | None = Field(default=None, max_length=120)
    shipping_line: str | None = Field(default=None, max_length=120)
    assigned_location_id: int | None = None
    assigned_bin: str | None = Field(default=None, max_length=64)
    assigned_staff_id: int | None = None
    assigned_staff_name: str | None = Field(default=None, max_length=120)
    assigned_equipment_id: int | None = None
    assigned_equipment_name: str | None = Field(default=None, max_length=120)
    workflow_state: str = Field(default="Manual", max_length=40)


class CargoCreate(CargoBase):
    pass


class CargoUpdate(BaseModel):
    manifest_number: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, max_length=40)
    weight_kg: float | None = Field(default=None, ge=0)
    supplier_id: int | None = None
    supplier_name: str | None = Field(default=None, max_length=120)
    shipping_line: str | None = Field(default=None, max_length=120)
    assigned_location_id: int | None = None
    assigned_bin: str | None = Field(default=None, max_length=64)
    assigned_staff_id: int | None = None
    assigned_staff_name: str | None = Field(default=None, max_length=120)
    assigned_equipment_id: int | None = None
    assigned_equipment_name: str | None = Field(default=None, max_length=120)
    workflow_state: str | None = Field(default=None, max_length=40)


class CargoRead(CargoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShipmentItem(BaseModel):
    sku: str = Field(..., max_length=64)
    item_name: str = Field(..., max_length=120)
    description: str | None = Field(default=None, max_length=255)
    quantity: int = Field(..., ge=1)
    unit: str = Field(default="units", max_length=32)


class CargoIntakeRequest(BaseModel):
    manifest_number: str = Field(..., max_length=64)
    description: str = Field(..., max_length=255)
    supplier_id: int
    weight_kg: float = Field(..., ge=0)
    preferred_zone: str | None = Field(default=None, max_length=32)
    equipment_type: str = Field(default="Forklift", max_length=64)
    staff_role: str = Field(default="Worker", max_length=64)
    inspection_completed: bool = False
    items: list[ShipmentItem] = Field(..., min_length=1)
