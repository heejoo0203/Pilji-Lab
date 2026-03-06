from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class VWorldParcelFeature:
    pnu: str
    geometry_json: str
    address: str
    price_current: int | None
    price_year: str | None


@dataclass
class ZoneParcelComputed:
    pnu: str
    lat: float | None
    lng: float | None
    area_sqm: float
    overlap_ratio: float
    price_current: int | None
    price_year: str | None
    jibun_address: str
    road_address: str
    land_category_name: str | None
    purpose_area_name: str | None
    geometry_geojson: str | None


@dataclass
class PreparedZonePreview:
    zone_name: str
    threshold: float
    coordinates: list[tuple[float, float]]
    zone_wkt: str
    zone_area_sqm: float
    parcels: list[ZoneParcelComputed]
    summary: dict[str, Any]
    generated_at: datetime
