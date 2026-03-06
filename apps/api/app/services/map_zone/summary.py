from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.zone_analysis import ZoneAnalysis
from app.models.zone_analysis_parcel import ZoneAnalysisParcel

from .domain import ZoneParcelComputed


def calculate_summary(parcels: list[ZoneParcelComputed]) -> dict[str, Any]:
    price_years = [item.price_year for item in parcels if item.price_year and item.price_current is not None]
    base_year = max(price_years) if price_years else None

    parcel_count = len(parcels)
    counted = [
        item
        for item in parcels
        if item.price_current is not None and item.price_year is not None and item.price_year == base_year
    ]
    counted_parcel_count = len(counted)
    zone_area_sqm = round(sum(float(item.area_sqm or 0.0) for item in parcels), 2)
    unit_price_sum = sum(int(item.price_current or 0) for item in counted)
    assessed_total_price = sum(int(round(item.area_sqm * int(item.price_current or 0))) for item in counted)

    return {
        "base_year": base_year,
        "zone_area_sqm": zone_area_sqm,
        "parcel_count": parcel_count,
        "counted_parcel_count": counted_parcel_count,
        "excluded_parcel_count": 0,
        "unit_price_sum": unit_price_sum,
        "assessed_total_price": assessed_total_price,
    }


def recalculate_zone_summary(db: Session, analysis: ZoneAnalysis) -> None:
    rows = db.query(ZoneAnalysisParcel).filter(ZoneAnalysisParcel.zone_analysis_id == analysis.id).all()
    included_rows = [row for row in rows if row.included]
    years = [row.price_year for row in included_rows if row.price_year and row.price_current is not None]
    base_year = max(years) if years else None

    counted_rows = [
        row for row in included_rows if row.price_current is not None and row.price_year is not None and row.price_year == base_year
    ]

    analysis.base_year = base_year
    analysis.zone_area_sqm = round(sum(float(row.area_sqm or 0.0) for row in included_rows), 2)
    analysis.parcel_count = len(included_rows)
    analysis.excluded_parcel_count = len(rows) - len(included_rows)
    analysis.counted_parcel_count = len(counted_rows)
    analysis.unit_price_sum = sum(int(row.price_current or 0) for row in counted_rows)
    analysis.assessed_total_price = sum(int(round(float(row.area_sqm or 0.0) * int(row.price_current or 0))) for row in counted_rows)
    analysis.updated_at = datetime.now(timezone.utc)
    db.add(analysis)


def get_zone_analysis_or_404(db: Session, *, user_id: str, zone_id: str) -> ZoneAnalysis:
    analysis = db.query(ZoneAnalysis).filter(ZoneAnalysis.id == zone_id, ZoneAnalysis.user_id == user_id).first()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ZONE_ANALYSIS_NOT_FOUND", "message": "구역 분석 결과를 찾을 수 없습니다."},
        )
    return analysis


def calculate_estimated_total_price(area_sqm: float | None, price_current: int | None) -> int | None:
    if area_sqm is None or price_current is None:
        return None
    return int(round(float(area_sqm) * int(price_current)))


def calculate_average_unit_price(*, assessed_total_price: int, zone_area_sqm: float) -> int | None:
    if zone_area_sqm <= 0:
        return None
    return int(round(assessed_total_price / zone_area_sqm))


def to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    text_value = str(value).replace(",", "").strip()
    if not text_value:
        return None
    try:
        return int(float(text_value))
    except (TypeError, ValueError):
        return None


def to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()
