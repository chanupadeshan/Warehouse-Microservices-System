from datetime import datetime
from sqlalchemy.orm import Session
from . import models, schemas


def create_supplier(db: Session, supplier_in: schemas.SupplierCreate) -> models.Supplier:
    supplier = models.Supplier(**supplier_in.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def get_suppliers(db: Session, skip: int = 0, limit: int = 100) -> list[models.Supplier]:
    return db.query(models.Supplier).offset(skip).limit(limit).all()


def get_supplier_by_id(db: Session, supplier_id: int) -> models.Supplier | None:
    return db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()


def update_supplier(db: Session, supplier: models.Supplier, supplier_in: schemas.SupplierUpdate) -> models.Supplier:
    data = supplier_in.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(supplier, key, value)

    supplier.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(supplier)
    return supplier


def delete_supplier(db: Session, supplier: models.Supplier) -> None:
    db.delete(supplier)
    db.commit()