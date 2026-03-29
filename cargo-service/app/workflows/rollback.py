import httpx
from fastapi import HTTPException

from app.config import (
    EQUIPMENT_SERVICE_URL,
    INVENTORY_SERVICE_URL,
    LOCATION_SERVICE_URL,
    STAFF_SERVICE_URL,
)
from app.workflows.clients import request_service
from app.workflows.progress import IntakeProgress


async def rollback_workflow(client: httpx.AsyncClient, progress: IntakeProgress) -> None:
    if progress.inventory_updated and progress.inventory_release_items:
        try:
            await request_service(
                client,
                "POST",
                INVENTORY_SERVICE_URL,
                "/inventory/release",
                json={"items": progress.inventory_release_items},
                operation="Inventory rollback failed",
            )
        except HTTPException:
            pass

    if progress.staff_member and progress.staff_assigned:
        try:
            await request_service(
                client,
                "POST",
                STAFF_SERVICE_URL,
                f"/staff/{progress.staff_member['id']}/release",
                operation="Staff rollback failed",
            )
        except HTTPException:
            pass

    if progress.equipment and progress.equipment_assigned:
        try:
            await request_service(
                client,
                "POST",
                EQUIPMENT_SERVICE_URL,
                f"/equipment/{progress.equipment['id']}/release",
                operation="Equipment rollback failed",
            )
        except HTTPException:
            pass

    if progress.location and progress.location_reserved:
        try:
            await request_service(
                client,
                "POST",
                LOCATION_SERVICE_URL,
                f"/locations/{progress.location['id']}/release",
                operation="Location rollback failed",
            )
        except HTTPException:
            pass
