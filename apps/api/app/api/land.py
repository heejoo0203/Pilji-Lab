from fastapi import APIRouter

from app.schemas.land import LandLookupRequest, LandLookupResponse
from app.services.vworld_service import lookup_land_prices

router = APIRouter(prefix="/api/v1/land", tags=["land"])


@router.post("/single", response_model=LandLookupResponse)
def lookup_single(payload: LandLookupRequest) -> LandLookupResponse:
    return lookup_land_prices(payload)
