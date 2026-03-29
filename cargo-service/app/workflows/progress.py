from dataclasses import dataclass, field

from app.schemas import CargoIntakeRequest


@dataclass
class IntakeProgress:
    supplier_validation: dict[str, object] = field(default_factory=dict)
    location: dict[str, object] | None = None
    staff_member: dict[str, object] | None = None
    equipment: dict[str, object] | None = None
    inventory_items: list[dict[str, object]] = field(default_factory=list)
    location_reserved: bool = False
    staff_assigned: bool = False
    equipment_assigned: bool = False
    inventory_updated: bool = False
    inventory_release_items: list[dict[str, object]] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: CargoIntakeRequest) -> "IntakeProgress":
        return cls(
            inventory_release_items=[
                {"sku": item.sku, "quantity": item.quantity}
                for item in payload.items
            ]
        )
