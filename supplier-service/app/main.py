from fastapi import FastAPI

from .database import engine
from . import models
from .routes.suppliers import router as suppliers_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Supplier Service",
    version="1.0.0",
    description="Manages supplier/vendor information for the warehouse system.",
)

app.include_router(suppliers_router)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "supplier-service"}