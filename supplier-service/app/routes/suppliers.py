from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db
from .. import crud, schemas

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.post("", response_model=schemas.SupplierOut, status_code=status.HTTP_201_CREATED)
def create_supplier(payload: schemas.SupplierCreate, db: Session = Depends(get_db)):
    return crud.create_supplier(db, payload)


@router.get("", response_model=list[schemas.SupplierOut])
def list_suppliers(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    return crud.get_suppliers(db, skip=skip, limit=limit)


@router.get("/{supplier_id}", response_model=schemas.SupplierOut)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = crud.get_supplier_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.put("/{supplier_id}", response_model=schemas.SupplierOut)
def update_supplier(supplier_id: int, payload: schemas.SupplierUpdate, db: Session = Depends(get_db)):
    supplier = crud.get_supplier_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return crud.update_supplier(db, supplier, payload)


@router.delete("/{supplier_id}")
def delete_inactive_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = crud.get_supplier_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    # Assignment requirement: delete inactive supplier
    if supplier.contract_status != "Inactive":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Supplier can only be deleted when contract_status is 'Inactive'",
        )

    crud.delete_supplier(db, supplier)
    return {"detail": "Supplier deleted"}