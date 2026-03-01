from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(title="autoLV API", version="0.1.0")
app.include_router(health_router)


@app.get("/")
def read_root() -> dict:
    return {"service": "autoLV-api", "status": "ok"}
