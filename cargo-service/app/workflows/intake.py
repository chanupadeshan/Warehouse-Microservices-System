import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import (
    EQUIPMENT_SERVICE_URL,
    HEAVY_CARGO_THRESHOLD_KG,
    INVENTORY_SERVICE_URL,
    LOCATION_SERVICE_URL,
    STAFF_SERVICE_URL,
    SUPPLIER_SERVICE_URL,
)
from app.schemas import CargoIntakeRequest, CargoRead
from app.workflows.cargo_state import create_pending_cargo, persist_cargo
from app.workflows.clients import request_service
from app.workflows.progress import IntakeProgress
from app.workflows.rollback import rollback_workflow


def total_quantity(payload: CargoIntakeRequest) -> int:
    return sum(item.quantity for item in payload.items)


def final_cargo_status(payload: CargoIntakeRequest) -> str:
    return "Inspected" if payload.inspection_completed else "Stored"


async def verify_supplier(
    client: httpx.AsyncClient,
    supplier_id: int,
) -> dict[str, object]:
    return await request_service(
        client,
        "GET",
        SUPPLIER_SERVICE_URL,
        f"/suppliers/{supplier_id}/validate",
        operation="Supplier verification failed",
    )


async def reserve_location(
    client: httpx.AsyncClient,
    payload: CargoIntakeRequest,
) -> dict[str, object]:
    return await request_service(
        client,
        "POST",
        LOCATION_SERVICE_URL,
        "/locations/reserve",
        json={
            "zone_code": payload.preferred_zone,
            "capacity_required": total_quantity(payload),
            "notes": f"Reserved for cargo {payload.manifest_number}",
        },
        operation="Location reservation failed",
    )


async def assign_staff(
    client: httpx.AsyncClient,
    payload: CargoIntakeRequest,
) -> dict[str, object]:
    return await request_service(
        client,
        "POST",
        STAFF_SERVICE_URL,
        "/staff/assign",
        json={
            "role": payload.staff_role,
            "assigned_task": f"Unload and store cargo {payload.manifest_number}",
        },
        operation="Staff assignment failed",
    )


def staff_display_name(staff_member: dict[str, object]) -> str:
    full_name = staff_member.get("full_name")
    if isinstance(full_name, str) and full_name.strip():
        return full_name

    first_name = str(staff_member.get("first_name", "")).strip()
    last_name = str(staff_member.get("last_name", "")).strip()
    return " ".join(part for part in (first_name, last_name) if part)


async def assign_equipment(
    client: httpx.AsyncClient,
    payload: CargoIntakeRequest,
) -> dict[str, object]:
    return await request_service(
        client,
        "POST",
        EQUIPMENT_SERVICE_URL,
        "/equipment/assign",
        json={
            "equipment_type": payload.equipment_type,
            "required_capacity_tons": payload.weight_kg / 1000,
        },
        operation="Equipment assignment failed",
    )


async def receive_inventory(
    client: httpx.AsyncClient,
    payload: CargoIntakeRequest,
    cargo_id: int,
    bin_code: str,
) -> list[dict[str, object]]:
    inventory_items = await request_service(
        client,
        "POST",
        INVENTORY_SERVICE_URL,
        "/inventory/receive",
        json={
            "cargo_id": cargo_id,
            "bin_code": bin_code,
            "status": "In Stock",
            "items": [item.model_dump() for item in payload.items],
        },
        operation="Inventory update failed",
    )
    return list(inventory_items)


def mark_supplier_failure(
    db: Session,
    cargo,
    supplier_validation: dict[str, object],
) -> None:
    persist_cargo(
        db,
        cargo,
        status="Verification Failed",
        workflow_state="Failed",
    )
    raise HTTPException(
        status_code=409,
        detail=supplier_validation.get("reason", "Supplier verification failed."),
    )


async def run_shipment_intake_workflow(
    payload: CargoIntakeRequest,
    db: Session,
) -> dict[str, object]:
    progress = IntakeProgress.from_payload(payload)
    cargo = create_pending_cargo(payload, db)

    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            progress.supplier_validation = await verify_supplier(client, payload.supplier_id)
            if not progress.supplier_validation.get("valid", False):
                mark_supplier_failure(db, cargo, progress.supplier_validation)

            persist_cargo(
                db,
                cargo,
                status="Pending Location Assignment",
                supplier_id=progress.supplier_validation["supplier_id"],
                supplier_name=progress.supplier_validation["supplier_name"],
                shipping_line=progress.supplier_validation["shipping_line"],
            )

            progress.location = await reserve_location(client, payload)
            progress.location_reserved = True
            persist_cargo(
                db,
                cargo,
                status="Pending Staff Assignment",
                assigned_location_id=progress.location["id"],
                assigned_bin=progress.location["bin_code"],
            )

            progress.staff_member = await assign_staff(client, payload)
            progress.staff_assigned = True
            persist_cargo(
                db,
                cargo,
                status=(
                    "Pending Equipment Assignment"
                    if payload.weight_kg >= HEAVY_CARGO_THRESHOLD_KG
                    else "Pending Inventory Update"
                ),
                assigned_staff_id=progress.staff_member["id"],
                assigned_staff_name=staff_display_name(progress.staff_member),
            )

            if payload.weight_kg >= HEAVY_CARGO_THRESHOLD_KG:
                progress.equipment = await assign_equipment(client, payload)
                progress.equipment_assigned = True
                persist_cargo(
                    db,
                    cargo,
                    status="Pending Inventory Update",
                    assigned_equipment_id=progress.equipment["id"],
                    assigned_equipment_name=progress.equipment["equipment_name"],
                )

            progress.inventory_items = await receive_inventory(
                client,
                payload,
                cargo.id,
                progress.location["bin_code"],
            )
            progress.inventory_updated = True
        except HTTPException:
            persist_cargo(db, cargo, workflow_state="Failed")
            await rollback_workflow(client, progress)
            raise

    persist_cargo(
        db,
        cargo,
        status=final_cargo_status(payload),
        workflow_state="Completed",
        assigned_equipment_id=progress.equipment["id"] if progress.equipment else None,
        assigned_equipment_name=(
            progress.equipment["equipment_name"] if progress.equipment else None
        ),
    )

    return {
        "cargo": CargoRead.model_validate(cargo).model_dump(mode="json"),
        "supplier": progress.supplier_validation,
        "location": progress.location,
        "inventory_items": progress.inventory_items,
        "equipment": progress.equipment,
        "staff": progress.staff_member,
    }
