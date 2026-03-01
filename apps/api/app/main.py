from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.api.auth import router as auth_router
from app.api.bulk import router as bulk_router
from app.api.health import router as health_router
from app.api.land import router as land_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


def _create_tables() -> None:
    # Import models before metadata creation.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def _migrate_schema() -> None:
    with engine.begin() as conn:
        inspector = inspect(conn)
        if "users" in inspector.get_table_names():
            columns = {col["name"] for col in inspector.get_columns("users")}
            if "profile_image_path" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN profile_image_path VARCHAR(500)"))


def _ensure_runtime_dirs() -> None:
    Path(settings.profile_image_dir).resolve().mkdir(parents=True, exist_ok=True)


_ensure_runtime_dirs()
app = FastAPI(title=settings.app_name, version="0.3.0")
allow_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(land_router)
app.include_router(bulk_router)
app.mount(
    "/media/profile",
    StaticFiles(directory=str(Path(settings.profile_image_dir).resolve())),
    name="profile-media",
)


@app.on_event("startup")
def on_startup() -> None:
    _ensure_runtime_dirs()
    _create_tables()
    _migrate_schema()


@app.get("/")
def read_root() -> dict:
    return {"service": "autoLV-api", "status": "ok"}
