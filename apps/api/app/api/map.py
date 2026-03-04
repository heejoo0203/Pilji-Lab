from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.map import MapClickRequest, MapLookupResponse
from app.services.map_service import export_map_csv, lookup_map_by_click

router = APIRouter(prefix="/api/v1/map", tags=["map"])


@router.post("/click", response_model=MapLookupResponse)
def map_click_lookup(
    payload: MapClickRequest,
    db: Session = Depends(get_db),
) -> MapLookupResponse:
    return lookup_map_by_click(db=db, payload=payload)


@router.get("/export")
def export_map_lookup_csv(
    pnu: str = Query(..., description="필지 고유번호(PNU)"),
    db: Session = Depends(get_db),
):
    return export_map_csv(db=db, pnu=pnu)
