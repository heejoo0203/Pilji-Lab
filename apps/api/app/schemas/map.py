from pydantic import BaseModel, Field

from app.schemas.land import LandResultRow


class MapClickRequest(BaseModel):
    lat: float = Field(description="위도")
    lng: float = Field(description="경도")


class MapLookupResponse(BaseModel):
    lat: float
    lng: float
    pnu: str
    address_summary: str
    area: float | None
    price_current: int | None
    price_previous: int | None
    growth_rate: float | None
    estimated_total_price: int | None
    nearby_avg_price: int | None
    nearby_radius_m: int
    cache_hit: bool
    rows: list[LandResultRow]
