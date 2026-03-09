from __future__ import annotations

from datetime import datetime, timezone
from statistics import median

from app.core.config import settings

from .domain import ZoneParcelComputed

ZONE_AI_MODEL_VERSION = "zone-ai-heuristic-v1.0.0"


def enrich_zone_ai(parcels: list[ZoneParcelComputed]) -> dict[str, int | str | None]:
    if not settings.map_zone_ai_enabled or not parcels:
        return {
            "ai_model_version": None,
            "ai_report_text": None,
            "ai_recommended_include_count": 0,
            "ai_uncertain_count": 0,
            "ai_excluded_count": 0,
            "anomaly_parcel_count": 0,
        }

    current_year = datetime.now(timezone.utc).year
    price_values = [int(item.price_current) for item in parcels if item.price_current is not None]
    median_price = median(price_values) if price_values else None

    include_count = 0
    uncertain_count = 0
    excluded_count = 0
    anomaly_count = 0

    for parcel in parcels:
        recommendation, ai_score, reason_codes, reason_text = _recommend_parcel(parcel)
        anomaly_codes, anomaly_level = _detect_anomalies(parcel, current_year=current_year, median_price=median_price)
        building_confidence, household_confidence, floor_area_ratio_confidence = _resolve_confidence(parcel)

        parcel.ai_recommendation = recommendation
        parcel.ai_confidence_score = ai_score
        parcel.ai_reason_codes = reason_codes
        parcel.ai_reason_text = reason_text
        parcel.ai_model_version = ZONE_AI_MODEL_VERSION
        parcel.anomaly_codes = anomaly_codes
        parcel.anomaly_level = anomaly_level
        parcel.building_confidence = building_confidence
        parcel.household_confidence = household_confidence
        parcel.floor_area_ratio_confidence = floor_area_ratio_confidence

        if recommendation == "included":
            include_count += 1
        elif recommendation == "uncertain":
            uncertain_count += 1
        else:
            excluded_count += 1

        if anomaly_level and anomaly_level != "none":
            anomaly_count += 1

    return {
        "ai_model_version": ZONE_AI_MODEL_VERSION,
        "ai_report_text": _build_zone_ai_report(
            parcels,
            include_count=include_count,
            uncertain_count=uncertain_count,
            anomaly_count=anomaly_count,
        ),
        "ai_recommended_include_count": include_count,
        "ai_uncertain_count": uncertain_count,
        "ai_excluded_count": excluded_count,
        "anomaly_parcel_count": anomaly_count,
    }


def _recommend_parcel(parcel: ZoneParcelComputed) -> tuple[str, float, list[str], str]:
    base_score = float(parcel.confidence_score or 0.0)
    bonus = 0.0
    reason_codes: list[str] = []

    if parcel.selected_by_rule:
        reason_codes.append("RULE_INCLUDED")
        if parcel.overlap_ratio >= 0.9:
            reason_codes.append("HIGH_OVERLAP")
        if parcel.centroid_in:
            reason_codes.append("CENTROID_IN_ZONE")
        if parcel.adjacency_bonus:
            reason_codes.append("ADJACENT_BLOCK")
        ai_score = round(max(base_score, 0.92), 4)
        return "included", ai_score, reason_codes, _render_reason_text(reason_codes)

    if parcel.overlap_ratio >= 0.65:
        bonus += 0.10
        reason_codes.append("MID_OVERLAP")
    if parcel.overlap_area_sqm >= max(90.0, parcel.area_sqm * 0.35):
        bonus += 0.06
        reason_codes.append("LARGE_INTERSECTION")
    if parcel.centroid_in:
        bonus += 0.08
        reason_codes.append("CENTROID_IN_ZONE")
    if parcel.adjacency_bonus:
        bonus += 0.06
        reason_codes.append("ADJACENT_BLOCK")

    ai_score = round(min(0.99, base_score + bonus), 4)
    include_threshold = max(0.5, min(0.98, settings.map_zone_ai_include_threshold))
    uncertain_threshold = max(0.3, min(include_threshold - 0.01, settings.map_zone_ai_uncertain_threshold))

    if ai_score >= include_threshold:
        recommendation = "included"
    elif ai_score >= uncertain_threshold:
        recommendation = "uncertain"
    else:
        recommendation = "excluded"
        if parcel.overlap_ratio < 0.25:
            reason_codes.append("LOW_OVERLAP")

    if not reason_codes:
        reason_codes.append("LOW_OVERLAP")
    return recommendation, ai_score, reason_codes, _render_reason_text(reason_codes)


def _render_reason_text(reason_codes: list[str]) -> str:
    reason_map = {
        "RULE_INCLUDED": "기본 포함 규칙을 충족했습니다.",
        "HIGH_OVERLAP": "필지 대부분이 구역 안에 포함됩니다.",
        "MID_OVERLAP": "겹치는 면적이 충분히 커서 포함 가능성이 높습니다.",
        "CENTROID_IN_ZONE": "필지 중심점이 구역 안에 있습니다.",
        "ADJACENT_BLOCK": "이미 포함된 필지와 인접해 있어 연속성이 높습니다.",
        "LARGE_INTERSECTION": "교집합 면적이 커서 사용자 의도상 포함 가능성이 높습니다.",
        "LOW_OVERLAP": "겹치는 면적이 작아 자동 포함 근거가 약합니다.",
    }
    unique_codes: list[str] = []
    for code in reason_codes:
        if code not in unique_codes:
            unique_codes.append(code)
    return " ".join(reason_map.get(code, code) for code in unique_codes)


def _detect_anomalies(
    parcel: ZoneParcelComputed,
    *,
    current_year: int,
    median_price: float | None,
) -> tuple[list[str], str]:
    codes: list[str] = []
    level = "none"

    if parcel.area_sqm <= 0:
        codes.append("INVALID_PARCEL_AREA")
    if parcel.building_count > 0 and (parcel.site_area_sqm is None or parcel.site_area_sqm <= 0):
        codes.append("MISSING_SITE_AREA")
    if parcel.floor_area_ratio is not None and parcel.floor_area_ratio > 800:
        codes.append("FAR_OUTLIER")
    if parcel.average_approval_year is not None and (parcel.average_approval_year < 1900 or parcel.average_approval_year > current_year):
        codes.append("APPROVAL_YEAR_OUTLIER")
    if (
        median_price
        and parcel.price_current is not None
        and median_price > 0
        and (parcel.price_current >= median_price * 4 or parcel.price_current <= median_price * 0.25)
    ):
        codes.append("PRICE_OUTLIER")
    if parcel.growth_rate is not None and abs(parcel.growth_rate) >= 100:
        codes.append("GROWTH_OUTLIER")

    if any(code in {"INVALID_PARCEL_AREA", "APPROVAL_YEAR_OUTLIER"} for code in codes):
        level = "critical"
    elif codes:
        level = "review"
    return codes, level


def _resolve_confidence(parcel: ZoneParcelComputed) -> tuple[str | None, str | None, str | None]:
    if parcel.building_count > 0 and parcel.site_area_sqm is not None:
        building_confidence = "high"
    elif parcel.building_count > 0:
        building_confidence = "medium"
    else:
        building_confidence = "low"

    if parcel.household_count is None:
        household_confidence = None
    elif parcel.household_count > 0 and parcel.primary_purpose_name and _is_residential(parcel.primary_purpose_name):
        household_confidence = "medium"
    else:
        household_confidence = "high"

    if parcel.floor_area_ratio is None:
        floor_area_ratio_confidence = None
    elif parcel.site_area_sqm is not None and parcel.total_floor_area_sqm is not None:
        floor_area_ratio_confidence = "high"
    else:
        floor_area_ratio_confidence = "medium"
    return building_confidence, household_confidence, floor_area_ratio_confidence


def _is_residential(name: str) -> bool:
    normalized = (name or "").strip()
    return any(keyword in normalized for keyword in ("주택", "아파트", "다세대", "연립", "다가구", "공동주택", "오피스텔"))


def _build_zone_ai_report(
    parcels: list[ZoneParcelComputed],
    *,
    include_count: int,
    uncertain_count: int,
    anomaly_count: int,
) -> str:
    counted = len(parcels)
    if counted == 0:
        return "AI 추천을 생성할 필지가 없습니다."
    if uncertain_count == 0 and anomaly_count == 0:
        return f"AI가 {counted}개 필지를 검토했고, 추천 포함 {include_count}건은 자동 반영 후보로 볼 수 있습니다."
    return (
        f"AI가 {counted}개 필지를 검토했습니다. 추천 포함 {include_count}건, 경계 검토 {uncertain_count}건, "
        f"이상치 검토 {anomaly_count}건입니다."
    )
