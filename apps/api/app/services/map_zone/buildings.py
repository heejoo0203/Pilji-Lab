from __future__ import annotations

from app.core.config import settings
from app.services.building_register_service import BuildingRegisterMetrics

from .domain import ZoneParcelComputed


def calculate_zone_building_summary(
    parcels: list[ZoneParcelComputed],
    *,
    metrics_by_pnu: dict[str, BuildingRegisterMetrics],
) -> dict[str, float | int | bool | str | None]:
    total_building_count = 0
    aged_building_count = 0
    approval_year_sum = 0
    approval_year_count = 0
    total_floor_area_sqm = 0.0
    total_site_area_sqm = 0.0
    undersized_parcel_count = 0
    seen_building_sources: set[str] = set()

    for parcel in parcels:
        metrics = metrics_by_pnu.get(parcel.pnu)
        if parcel.area_sqm < settings.map_zone_undersized_parcel_threshold_sqm:
            undersized_parcel_count += 1
        if metrics is None or not metrics.has_building_register:
            continue
        source_key = (metrics.source_pnu or parcel.pnu).strip() or parcel.pnu
        if source_key in seen_building_sources:
            continue
        seen_building_sources.add(source_key)
        total_building_count += metrics.building_count
        aged_building_count += metrics.aged_building_count
        approval_year_sum += metrics.approval_year_sum
        approval_year_count += metrics.approval_year_count
        if metrics.total_floor_area_sqm:
            total_floor_area_sqm += metrics.total_floor_area_sqm
        if metrics.site_area_sqm:
            total_site_area_sqm += metrics.site_area_sqm

    average_approval_year = round(approval_year_sum / approval_year_count) if approval_year_count else None
    aged_building_ratio = round((aged_building_count / total_building_count) * 100, 2) if total_building_count else 0.0
    average_floor_area_ratio = (
        round((total_floor_area_sqm / total_site_area_sqm) * 100, 2) if total_site_area_sqm > 0 and total_floor_area_sqm > 0 else 0.0
    )
    undersized_parcel_ratio = round((undersized_parcel_count / len(parcels)) * 100, 2) if parcels else None

    return {
        "total_building_count": total_building_count,
        "aged_building_count": aged_building_count,
        "aged_building_ratio": aged_building_ratio,
        "average_approval_year": average_approval_year,
        "total_floor_area_sqm": round(total_floor_area_sqm, 2) if total_floor_area_sqm > 0 else 0.0,
        "total_site_area_sqm": round(total_site_area_sqm, 2) if total_site_area_sqm > 0 else round(sum(parcel.area_sqm for parcel in parcels), 2),
        "average_floor_area_ratio": average_floor_area_ratio,
        "undersized_parcel_count": undersized_parcel_count,
        "undersized_parcel_ratio": undersized_parcel_ratio,
    }
