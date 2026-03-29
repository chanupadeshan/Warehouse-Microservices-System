from fastapi import FastAPI

from app.database import Base, engine
from app.routes import router

app = FastAPI(
    title="Cargo Service",
    version="1.0.0",
    description="Manage incoming cargo shipments with PostgreSQL persistence.",
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(router)
