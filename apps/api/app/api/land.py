from fastapi import APIRouter, Query

from app.schemas.land import LandLookupRequest, LandLookupResponse, RoadNameListResponse
from app.services.road_name_service import get_road_names
from app.services.vworld_service import lookup_land_prices

router = APIRouter(prefix="/api/v1/land", tags=["land"])


@router.post("/single", response_model=LandLookupResponse)
def lookup_single(payload: LandLookupRequest) -> LandLookupResponse:
    return lookup_land_prices(payload)


@router.get("/road-names", response_model=RoadNameListResponse)
def lookup_road_names(
    sido: str = Query(..., description="시/도"),
    sigungu: str = Query(..., description="시/군/구"),
    initial: str = Query(..., description="초성(예: ㄱ, ㄴ, ㄷ)"),
) -> RoadNameListResponse:
    roads = get_road_names(sido=sido, sigungu=sigungu, initial=initial)
    return RoadNameListResponse(sido=sido, sigungu=sigungu, initial=initial, roads=roads)
