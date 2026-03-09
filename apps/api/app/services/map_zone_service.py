from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.zone_ai_feedback import ZoneAIFeedback
from app.models.zone_analysis import ZoneAnalysis
from app.models.zone_analysis_parcel import ZoneAnalysisParcel
from app.schemas.map import (
    MapCoordinate,
    MapZoneAnalyzeRequest,
    MapZoneDeleteResponse,
    MapZoneListItem,
    MapZoneListResponse,
    MapZoneParcelDecisionRequest,
    MapZoneParcelExcludeRequest,
    MapZoneParcelItem,
    MapZoneResponse,
    MapZoneSaveRequest,
    MapZoneSummary,
    MapZoneUpdateRequest,
)
from app.services.building_register_service import fetch_building_register_metrics_batch
from app.services.map_zone.ai import enrich_zone_ai
from app.services.map_zone.buildings import calculate_zone_building_summary
from app.services.map_zone.domain import PreparedZonePreview
from app.services.map_zone.geometry import (
    calculate_bbox,
    calculate_zone_area,
    coordinates_to_wkt,
    normalize_polygon_coordinates,
    normalize_zone_name,
    require_postgres,
    resolve_overlap_threshold,
    validate_zone_geometry,
    zone_wkt_to_coordinates,
)
from app.services.map_zone.parcels import (
    compose_zone_parcels,
    fetch_saved_zone_parcel_metadata,
    fetch_vworld_parcel_features,
    fetch_zone_land_metadata,
    query_overlapped_parcels,
    upsert_parcel_geometries,
)
from app.services.map_zone.summary import (
    ZONE_ANALYSIS_ALGORITHM_VERSION,
    calculate_average_unit_price,
    calculate_estimated_total_price,
    calculate_summary,
    get_zone_analysis_or_404,
    recalculate_zone_summary,
    to_iso,
)


def _calculate_growth_rate(current_price: int | None, previous_price: int | None) -> float | None:
    if current_price is None or previous_price in (None, 0):
        return None
    return round(((current_price - previous_price) / previous_price) * 100, 2)


def _deserialize_codes(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if item]
    except (TypeError, ValueError):
        return []
    return []


def _serialize_codes(value: list[str] | None) -> str | None:
    if not value:
        return None
    return json.dumps(value, ensure_ascii=False)


def _resolve_preview_included_set(
    preview: PreparedZonePreview,
    *,
    included_pnu_list: list[str] | None = None,
    excluded_pnu_list: list[str] | None = None,
) -> set[str]:
    included_set = {item.pnu for item in preview.parcels if item.selected_by_rule}
    included_set.update(pnu.strip() for pnu in (included_pnu_list or []) if pnu.strip())
    included_set.difference_update(pnu.strip() for pnu in (excluded_pnu_list or []) if pnu.strip())
    return included_set


def _resolve_row_inclusion_state(
    *,
    selected_by_rule: bool,
    included: bool,
    ai_recommendation: str | None,
    decision_origin: str | None,
) -> tuple[str, str, bool]:
    normalized_origin = (decision_origin or "").strip().lower() or "user"
    if included:
        if selected_by_rule:
            return "rule_overlap", "rule", False
        if normalized_origin == "ai" and ai_recommendation == "included":
            return "ai_included", "ai", True
        return "user_included", normalized_origin, False
    if selected_by_rule:
        return "user_excluded", normalized_origin, False
    if ai_recommendation == "included":
        return "ai_not_applied", normalized_origin, False
    return "excluded", normalized_origin, False


def _append_ai_feedback(
    db: Session,
    *,
    zone_analysis_id: str,
    user_id: str,
    pnu: str,
    ai_model_version: str | None,
    ai_recommendation: str | None,
    final_decision: str,
    decision_origin: str,
) -> None:
    db.add(
        ZoneAIFeedback(
            zone_analysis_id=zone_analysis_id,
            pnu=pnu,
            user_id=user_id,
            ai_model_version=ai_model_version,
            ai_recommendation=ai_recommendation,
            final_decision=final_decision,
            decision_origin=decision_origin,
        )
    )


def _fetch_parcel_price_snapshot_map(db: Session, pnu_list: list[str]) -> dict[str, dict[str, int | None]]:
    unique_pnu_list = [pnu for pnu in dict.fromkeys(pnu_list) if pnu]
    if not unique_pnu_list:
        return {}
    bind_params: dict[str, object] = {}
    placeholders: list[str] = []
    for idx, pnu in enumerate(unique_pnu_list):
        key = f"snapshot_pnu_{idx}"
        bind_params[key] = pnu
        placeholders.append(f":{key}")
    rows = db.execute(
        text(
            f"""
            SELECT pnu, price_current, price_previous
            FROM parcels
            WHERE pnu IN ({", ".join(placeholders)})
            """
        ),
        bind_params,
    ).mappings().all()
    return {
        str(row.get("pnu")): {
            "price_current": int(row.get("price_current")) if row.get("price_current") is not None else None,
            "price_previous": int(row.get("price_previous")) if row.get("price_previous") is not None else None,
        }
        for row in rows
        if row.get("pnu")
    }


def analyze_zone(
    db: Session,
    *,
    payload: MapZoneAnalyzeRequest,
) -> MapZoneResponse:
    preview = _prepare_zone_preview(db, payload=payload)
    return _build_zone_response(preview=preview, zone_id=None, is_saved=False)


def save_zone_analysis(
    db: Session,
    *,
    user_id: str,
    payload: MapZoneSaveRequest,
) -> MapZoneResponse:
    preview = _prepare_zone_preview(
        db,
        payload=MapZoneAnalyzeRequest(
            zone_name=payload.zone_name,
            coordinates=payload.coordinates,
            overlap_threshold=payload.overlap_threshold,
        ),
    )
    excluded_pnu_set = {pnu.strip() for pnu in payload.excluded_pnu_list if pnu.strip()}
    explicit_included_pnu_set = {pnu.strip() for pnu in payload.included_pnu_list if pnu.strip()}
    final_included_pnu_set = _resolve_preview_included_set(
        preview,
        included_pnu_list=list(explicit_included_pnu_set),
        excluded_pnu_list=list(excluded_pnu_set),
    )
    analysis = ZoneAnalysis(
        user_id=user_id,
        zone_name=preview.zone_name,
        zone_wkt=preview.zone_wkt,
        overlap_threshold=preview.threshold,
        zone_area_sqm=preview.summary["zone_area_sqm"],
        base_year=preview.summary["base_year"],
        parcel_count=preview.summary["parcel_count"],
        counted_parcel_count=preview.summary["counted_parcel_count"],
        excluded_parcel_count=preview.summary["excluded_parcel_count"],
        unit_price_sum=preview.summary["unit_price_sum"],
        assessed_total_price=preview.summary["assessed_total_price"],
    )
    db.add(analysis)
    db.flush()

    for item in preview.parcels:
        included = item.pnu in final_included_pnu_set
        row_decision_origin = (
            "ai"
            if item.pnu in explicit_included_pnu_set and item.ai_recommendation == "included"
            else "user"
        )
        inclusion_mode, selection_origin, ai_applied = _resolve_row_inclusion_state(
            selected_by_rule=item.selected_by_rule,
            included=included,
            ai_recommendation=item.ai_recommendation,
            decision_origin=row_decision_origin,
        )
        excluded_reason = None
        if not included:
            excluded_reason = "저장 전 사용자 제외" if item.selected_by_rule else "자동 제외"
        db.add(
            ZoneAnalysisParcel(
                zone_analysis_id=analysis.id,
                pnu=item.pnu,
                jibun_address=item.jibun_address,
                road_address=item.road_address,
                land_category_name=item.land_category_name,
                purpose_area_name=item.purpose_area_name,
                area_sqm=item.area_sqm,
                overlap_area_sqm=item.overlap_area_sqm,
                price_current=item.price_current,
                price_year=item.price_year,
                overlap_ratio=item.overlap_ratio,
                centroid_in=item.centroid_in,
                selected_by_rule=item.selected_by_rule,
                inclusion_mode=inclusion_mode,
                confidence_score=item.confidence_score,
                ai_recommendation=item.ai_recommendation,
                ai_confidence_score=item.ai_confidence_score,
                ai_reason_codes=_serialize_codes(item.ai_reason_codes),
                ai_reason_text=item.ai_reason_text,
                ai_model_version=item.ai_model_version,
                ai_applied=ai_applied,
                selection_origin=selection_origin,
                anomaly_codes=_serialize_codes(item.anomaly_codes),
                anomaly_level=item.anomaly_level,
                building_confidence=item.building_confidence,
                household_confidence=item.household_confidence,
                floor_area_ratio_confidence=item.floor_area_ratio_confidence,
                included=included,
                excluded_reason=excluded_reason,
                excluded_at=None if included else preview.generated_at,
                lat=item.lat,
                lng=item.lng,
            )
        )
        if included != item.selected_by_rule:
            _append_ai_feedback(
                db,
                zone_analysis_id=analysis.id,
                user_id=user_id,
                pnu=item.pnu,
                ai_model_version=item.ai_model_version,
                ai_recommendation=item.ai_recommendation,
                final_decision="included" if included else "excluded",
                decision_origin=selection_origin,
            )

    recalculate_zone_summary(db, analysis)
    db.commit()
    return get_zone_detail(db, user_id=user_id, zone_id=analysis.id)


def get_zone_detail(db: Session, *, user_id: str, zone_id: str) -> MapZoneResponse:
    analysis = get_zone_analysis_or_404(db, user_id=user_id, zone_id=zone_id)

    rows = (
        db.query(ZoneAnalysisParcel)
        .filter(ZoneAnalysisParcel.zone_analysis_id == zone_id)
        .order_by(ZoneAnalysisParcel.included.desc(), ZoneAnalysisParcel.overlap_ratio.desc(), ZoneAnalysisParcel.pnu.asc())
        .all()
    )
    base_year = analysis.base_year
    response_zone_area_sqm = round(sum(float(row.area_sqm or 0.0) for row in rows if row.included), 2)
    response_overlap_area_total = round(sum(float(row.overlap_area_sqm or 0.0) for row in rows if row.included), 2)
    parcel_metadata_map = fetch_saved_zone_parcel_metadata(db, [row.pnu for row in rows])
    price_snapshot_map = _fetch_parcel_price_snapshot_map(db, [row.pnu for row in rows])
    missing_land_metadata_pnu = [row.pnu for row in rows if not row.land_category_name and not row.purpose_area_name]
    live_land_metadata_map = fetch_zone_land_metadata(missing_land_metadata_pnu) if missing_land_metadata_pnu else {}
    building_batch = fetch_building_register_metrics_batch(
        db,
        parcel_area_by_pnu={row.pnu: float(row.area_sqm or 0.0) for row in rows},
    )
    parcels = [
        MapZoneParcelItem(
            pnu=row.pnu,
            jibun_address=row.jibun_address,
            road_address=row.road_address,
            land_category_name=row.land_category_name or live_land_metadata_map.get(row.pnu, {}).get("land_category_name"),
            purpose_area_name=row.purpose_area_name or live_land_metadata_map.get(row.pnu, {}).get("purpose_area_name"),
            geometry_geojson=parcel_metadata_map.get(row.pnu),
            area_sqm=float(row.area_sqm or 0.0),
            overlap_area_sqm=float(row.overlap_area_sqm or 0.0),
            price_current=row.price_current,
            price_year=row.price_year,
            estimated_total_price=calculate_estimated_total_price(row.area_sqm, row.price_current),
            geometry_estimated_total_price=calculate_estimated_total_price(row.overlap_area_sqm, row.price_current),
            overlap_ratio=round(float(row.overlap_ratio or 0.0), 4),
            centroid_in=bool(row.centroid_in),
            selected_by_rule=bool(row.selected_by_rule),
            inclusion_mode=str(row.inclusion_mode or ("rule_overlap" if row.included else "excluded")),
            confidence_score=round(float(row.confidence_score or 0.0), 4),
            ai_recommendation=row.ai_recommendation,
            ai_confidence_score=round(float(row.ai_confidence_score), 4) if row.ai_confidence_score is not None else None,
            ai_reason_codes=_deserialize_codes(row.ai_reason_codes),
            ai_reason_text=row.ai_reason_text,
            ai_model_version=row.ai_model_version,
            ai_applied=bool(row.ai_applied),
            selection_origin=str(row.selection_origin or "rule"),
            anomaly_codes=_deserialize_codes(row.anomaly_codes),
            anomaly_level=row.anomaly_level,
            building_confidence=row.building_confidence,
            household_confidence=row.household_confidence,
            floor_area_ratio_confidence=row.floor_area_ratio_confidence,
            included=bool(row.included),
            counted_in_summary=bool(
                row.included and row.price_current is not None and row.price_year is not None and row.price_year == base_year
            ),
            lat=row.lat,
            lng=row.lng,
            building_count=building_batch.metrics_by_pnu.get(row.pnu, {}).building_count if row.pnu in building_batch.metrics_by_pnu else 0,
            aged_building_count=building_batch.metrics_by_pnu.get(row.pnu, {}).aged_building_count if row.pnu in building_batch.metrics_by_pnu else 0,
            average_approval_year=(
                building_batch.metrics_by_pnu.get(row.pnu, {}).average_approval_year
                if row.pnu in building_batch.metrics_by_pnu
                else None
            ),
            price_previous=price_snapshot_map.get(row.pnu, {}).get("price_previous"),
            growth_rate=_calculate_growth_rate(
                row.price_current,
                price_snapshot_map.get(row.pnu, {}).get("price_previous"),
            ),
            aged_building_ratio=(
                round((building_batch.metrics_by_pnu.get(row.pnu, {}).aged_building_count / building_batch.metrics_by_pnu.get(row.pnu, {}).building_count) * 100, 2)
                if row.pnu in building_batch.metrics_by_pnu and building_batch.metrics_by_pnu.get(row.pnu, {}).building_count
                else None
            ),
            site_area_sqm=(
                building_batch.metrics_by_pnu.get(row.pnu, {}).site_area_sqm
                if row.pnu in building_batch.metrics_by_pnu
                else None
            ),
            total_floor_area_sqm=(
                building_batch.metrics_by_pnu.get(row.pnu, {}).total_floor_area_sqm
                if row.pnu in building_batch.metrics_by_pnu
                else None
            ),
            floor_area_ratio=(
                building_batch.metrics_by_pnu.get(row.pnu, {}).floor_area_ratio
                if row.pnu in building_batch.metrics_by_pnu
                else None
            ),
            building_coverage_ratio=(
                building_batch.metrics_by_pnu.get(row.pnu, {}).building_coverage_ratio
                if row.pnu in building_batch.metrics_by_pnu
                else None
            ),
            household_count=(
                building_batch.metrics_by_pnu.get(row.pnu, {}).household_count
                if row.pnu in building_batch.metrics_by_pnu
                else None
            ),
            primary_purpose_name=(
                building_batch.metrics_by_pnu.get(row.pnu, {}).primary_purpose_name
                if row.pnu in building_batch.metrics_by_pnu
                else None
            ),
        )
        for row in rows
    ]
    building_summary = calculate_zone_building_summary(
        [item for item in parcels if item.included],
        metrics_by_pnu=building_batch.metrics_by_pnu,
    )
    geometry_assessed_total_price = sum(
        int(round(float(row.overlap_area_sqm or 0.0) * int(row.price_current or 0)))
        for row in rows
        if row.included and row.price_current is not None and row.price_year is not None and row.price_year == base_year
    )
    boundary_parcel_count = sum(1 for row in rows if str(row.inclusion_mode or "") == "boundary_candidate")
    summary = MapZoneSummary(
        zone_id=analysis.id,
        zone_name=analysis.zone_name,
        is_saved=True,
        base_year=analysis.base_year,
        overlap_threshold=round(float(analysis.overlap_threshold), 4),
        zone_area_sqm=response_zone_area_sqm,
        overlap_area_sqm_total=response_overlap_area_total,
        parcel_count=int(analysis.parcel_count),
        boundary_parcel_count=boundary_parcel_count,
        counted_parcel_count=int(analysis.counted_parcel_count),
        excluded_parcel_count=int(analysis.excluded_parcel_count),
        average_unit_price=calculate_average_unit_price(
            assessed_total_price=int(analysis.assessed_total_price),
            zone_area_sqm=response_zone_area_sqm,
        ),
        assessed_total_price=int(analysis.assessed_total_price),
        geometry_assessed_total_price=int(geometry_assessed_total_price),
        algorithm_version=ZONE_ANALYSIS_ALGORITHM_VERSION,
        ai_model_version=rows[0].ai_model_version if rows else None,
        ai_report_text=_build_saved_zone_ai_report(parcels),
        ai_recommended_include_count=sum(1 for row in parcels if row.ai_recommendation == "included"),
        ai_uncertain_count=sum(1 for row in parcels if row.ai_recommendation == "uncertain"),
        ai_excluded_count=sum(1 for row in parcels if row.ai_recommendation == "excluded"),
        anomaly_parcel_count=sum(1 for row in parcels if row.anomaly_level and row.anomaly_level != "none"),
        building_data_ready=building_batch.ready,
        building_data_message=building_batch.message,
        total_building_count=int(building_summary["total_building_count"]),
        aged_building_count=int(building_summary["aged_building_count"]),
        aged_building_ratio=building_summary["aged_building_ratio"],
        average_approval_year=building_summary["average_approval_year"],
        total_floor_area_sqm=building_summary["total_floor_area_sqm"],
        total_site_area_sqm=building_summary["total_site_area_sqm"],
        average_floor_area_ratio=building_summary["average_floor_area_ratio"],
        undersized_parcel_count=int(building_summary["undersized_parcel_count"]),
        undersized_parcel_ratio=building_summary["undersized_parcel_ratio"],
        created_at=to_iso(analysis.created_at),
        updated_at=to_iso(analysis.updated_at),
    )
    return MapZoneResponse(summary=summary, coordinates=zone_wkt_to_coordinates(analysis.zone_wkt), parcels=parcels)


def list_zone_analyses(db: Session, *, user_id: str, page: int, page_size: int) -> MapZoneListResponse:
    total_count = db.query(ZoneAnalysis).filter(ZoneAnalysis.user_id == user_id).count()
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    current_page = min(page, total_pages)
    offset = (current_page - 1) * page_size

    rows = (
        db.query(ZoneAnalysis)
        .filter(ZoneAnalysis.user_id == user_id)
        .order_by(ZoneAnalysis.updated_at.desc(), ZoneAnalysis.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    items = [
        MapZoneListItem(
            zone_id=row.id,
            zone_name=row.zone_name,
            base_year=row.base_year,
            parcel_count=int(row.parcel_count),
            assessed_total_price=int(row.assessed_total_price),
            created_at=to_iso(row.created_at),
            updated_at=to_iso(row.updated_at),
        )
        for row in rows
    ]
    return MapZoneListResponse(
        page=current_page,
        page_size=page_size,
        total_count=total_count,
        total_pages=total_pages,
        items=items,
    )


def exclude_zone_parcels(
    db: Session,
    *,
    user_id: str,
    zone_id: str,
    payload: MapZoneParcelExcludeRequest,
) -> MapZoneResponse:
    return update_zone_parcel_decisions(
        db,
        user_id=user_id,
        zone_id=zone_id,
        payload=MapZoneParcelDecisionRequest(
            include_pnu_list=[],
            exclude_pnu_list=payload.pnu_list,
            decision_origin="user",
            reason=payload.reason,
        ),
    )


def update_zone_parcel_decisions(
    db: Session,
    *,
    user_id: str,
    zone_id: str,
    payload: MapZoneParcelDecisionRequest,
) -> MapZoneResponse:
    analysis = get_zone_analysis_or_404(db, user_id=user_id, zone_id=zone_id)

    include_pnu_list = [pnu.strip() for pnu in payload.include_pnu_list if pnu.strip()]
    exclude_pnu_list = [pnu.strip() for pnu in payload.exclude_pnu_list if pnu.strip()]
    target_pnu_list = list(dict.fromkeys(include_pnu_list + exclude_pnu_list))
    if not target_pnu_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_PNU_LIST", "message": "포함 또는 제외할 필지를 선택해 주세요."},
        )

    now = datetime.now(timezone.utc)
    rows = (
        db.query(ZoneAnalysisParcel)
        .filter(
            ZoneAnalysisParcel.zone_analysis_id == zone_id,
            ZoneAnalysisParcel.pnu.in_(target_pnu_list),
        )
        .all()
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ZONE_PARCELS_NOT_FOUND", "message": "선택한 필지를 찾을 수 없습니다."},
        )

    include_pnu_set = set(include_pnu_list)
    exclude_pnu_set = set(exclude_pnu_list)
    decision_origin = (payload.decision_origin or "user").strip().lower() or "user"
    reason = (payload.reason or "사용자 수동 조정").strip()[:200] or "사용자 수동 조정"

    for row in rows:
        if row.pnu in include_pnu_set:
            row.included = True
            row.excluded_at = None
            row.excluded_reason = None
            row.inclusion_mode, row.selection_origin, row.ai_applied = _resolve_row_inclusion_state(
                selected_by_rule=bool(row.selected_by_rule),
                included=True,
                ai_recommendation=row.ai_recommendation,
                decision_origin=decision_origin,
            )
            row.updated_at = now
            _append_ai_feedback(
                db,
                zone_analysis_id=analysis.id,
                user_id=user_id,
                pnu=row.pnu,
                ai_model_version=row.ai_model_version,
                ai_recommendation=row.ai_recommendation,
                final_decision="included",
                decision_origin=row.selection_origin,
            )
        elif row.pnu in exclude_pnu_set:
            row.included = False
            row.excluded_at = now
            row.excluded_reason = reason
            row.inclusion_mode, row.selection_origin, row.ai_applied = _resolve_row_inclusion_state(
                selected_by_rule=bool(row.selected_by_rule),
                included=False,
                ai_recommendation=row.ai_recommendation,
                decision_origin=decision_origin,
            )
            row.updated_at = now
            _append_ai_feedback(
                db,
                zone_analysis_id=analysis.id,
                user_id=user_id,
                pnu=row.pnu,
                ai_model_version=row.ai_model_version,
                ai_recommendation=row.ai_recommendation,
                final_decision="excluded",
                decision_origin=row.selection_origin,
            )
        db.add(row)

    recalculate_zone_summary(db, analysis)
    db.commit()
    return get_zone_detail(db, user_id=user_id, zone_id=zone_id)


def update_zone_name(
    db: Session,
    *,
    user_id: str,
    zone_id: str,
    payload: MapZoneUpdateRequest,
) -> MapZoneResponse:
    analysis = get_zone_analysis_or_404(db, user_id=user_id, zone_id=zone_id)
    analysis.zone_name = normalize_zone_name(payload.zone_name)
    analysis.updated_at = datetime.now(timezone.utc)
    db.add(analysis)
    db.commit()
    return get_zone_detail(db, user_id=user_id, zone_id=zone_id)


def delete_zone_analysis(
    db: Session,
    *,
    user_id: str,
    zone_id: str,
) -> MapZoneDeleteResponse:
    analysis = get_zone_analysis_or_404(db, user_id=user_id, zone_id=zone_id)
    db.delete(analysis)
    db.commit()
    return MapZoneDeleteResponse(zone_id=zone_id, deleted=True)


def export_zone_csv(db: Session, *, user_id: str, zone_id: str) -> Response:
    response = get_zone_detail(db, user_id=user_id, zone_id=zone_id)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "zone_id",
            "zone_name",
            "base_year",
            "pnu",
            "jibun_address",
            "road_address",
            "area_sqm",
            "overlap_area_sqm",
            "price_current",
            "estimated_total_price",
            "geometry_estimated_total_price",
            "price_year",
            "building_count",
            "aged_building_count",
            "average_approval_year",
            "total_floor_area_sqm",
            "floor_area_ratio",
            "primary_purpose_name",
            "overlap_ratio",
            "centroid_in",
            "inclusion_mode",
            "confidence_score",
            "ai_recommendation",
            "ai_confidence_score",
            "selection_origin",
            "anomaly_level",
            "included",
            "counted_in_summary",
            "algorithm_version",
        ]
    )

    for row in response.parcels:
        writer.writerow(
            [
                response.summary.zone_id,
                response.summary.zone_name,
                response.summary.base_year or "",
                row.pnu,
                row.jibun_address,
                row.road_address,
                f"{row.area_sqm:.2f}",
                f"{row.overlap_area_sqm:.2f}",
                row.price_current or "",
                row.estimated_total_price or "",
                row.geometry_estimated_total_price or "",
                row.price_year or "",
                row.building_count,
                row.aged_building_count,
                row.average_approval_year or "",
                f"{row.total_floor_area_sqm:.2f}" if row.total_floor_area_sqm is not None else "",
                f"{row.floor_area_ratio:.2f}" if row.floor_area_ratio is not None else "",
                row.primary_purpose_name or "",
                f"{row.overlap_ratio:.4f}",
                "Y" if row.centroid_in else "N",
                row.inclusion_mode,
                f"{row.confidence_score:.4f}",
                row.ai_recommendation or "",
                f"{row.ai_confidence_score:.4f}" if row.ai_confidence_score is not None else "",
                row.selection_origin,
                row.anomaly_level or "",
                "Y" if row.included else "N",
                "Y" if row.counted_in_summary else "N",
                response.summary.algorithm_version,
            ]
        )

    filename = f"zone_{zone_id}.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _prepare_zone_preview(db: Session, *, payload: MapZoneAnalyzeRequest) -> PreparedZonePreview:
    require_postgres(db)
    zone_name = normalize_zone_name(payload.zone_name)
    threshold = resolve_overlap_threshold(payload.overlap_threshold)
    coordinates = normalize_polygon_coordinates(payload.coordinates)
    zone_wkt = coordinates_to_wkt(coordinates)

    drawn_zone_area_sqm = calculate_zone_area(db, zone_wkt)
    if drawn_zone_area_sqm > settings.map_zone_max_area_sqm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "ZONE_AREA_TOO_LARGE",
                "message": f"구역 면적은 최대 {int(settings.map_zone_max_area_sqm):,}㎡ 까지만 허용됩니다.",
            },
        )

    validate_zone_geometry(db, zone_wkt)
    bbox = calculate_bbox(coordinates)
    feature_map = fetch_vworld_parcel_features(bbox)
    upsert_parcel_geometries(db, list(feature_map.values()))
    overlapped = query_overlapped_parcels(db, zone_wkt=zone_wkt, threshold=threshold, pnu_list=list(feature_map.keys()))
    max_included_parcels = max(1, int(settings.map_zone_max_included_parcels))
    land_metadata_map = fetch_zone_land_metadata([row["pnu"] for row in overlapped])
    parcels = compose_zone_parcels(overlapped, feature_map, land_metadata_map, threshold=threshold)
    predicted_included_count = sum(1 for item in parcels if item.selected_by_rule)
    if predicted_included_count > max_included_parcels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "ZONE_TOO_MANY_INCLUDED_PARCELS",
                "message": (
                    f"구역 내 포함 후보 필지가 {predicted_included_count:,}건으로 너무 많습니다. "
                    f"현재는 최대 {max_included_parcels:,}필지까지 분석할 수 있습니다. "
                    "구역을 더 작게 나눠 조회해 주세요."
                ),
            },
        )
    price_snapshot_map = _fetch_parcel_price_snapshot_map(db, [item.pnu for item in parcels])
    building_batch = fetch_building_register_metrics_batch(
        db,
        parcel_area_by_pnu={item.pnu: item.area_sqm for item in parcels},
    )
    for item in parcels:
        metrics = building_batch.metrics_by_pnu.get(item.pnu)
        if metrics is None:
            continue
        item.building_count = metrics.building_count
        item.aged_building_count = metrics.aged_building_count
        item.average_approval_year = metrics.average_approval_year
        item.price_previous = price_snapshot_map.get(item.pnu, {}).get("price_previous")
        item.growth_rate = _calculate_growth_rate(item.price_current, item.price_previous)
        item.aged_building_ratio = round((metrics.aged_building_count / metrics.building_count) * 100, 2) if metrics.building_count else None
        item.site_area_sqm = metrics.site_area_sqm
        item.total_floor_area_sqm = metrics.total_floor_area_sqm
        item.floor_area_ratio = metrics.floor_area_ratio
        item.building_coverage_ratio = metrics.building_coverage_ratio
        item.household_count = metrics.household_count
        item.primary_purpose_name = metrics.primary_purpose_name
    ai_summary = enrich_zone_ai(parcels)
    summary = calculate_summary(parcels)
    return PreparedZonePreview(
        zone_name=zone_name,
        threshold=threshold,
        coordinates=coordinates,
        zone_wkt=zone_wkt,
        zone_area_sqm=summary["zone_area_sqm"],
        parcels=parcels,
        summary=summary,
        building_metrics_by_pnu=building_batch.metrics_by_pnu,
        building_data_ready=building_batch.ready,
        building_data_message=building_batch.message,
        ai_report_text=ai_summary["ai_report_text"] if isinstance(ai_summary["ai_report_text"], str) else None,
        ai_model_version=ai_summary["ai_model_version"] if isinstance(ai_summary["ai_model_version"], str) else None,
        generated_at=datetime.now(timezone.utc),
    )


def _build_zone_response(
    *,
    preview: PreparedZonePreview,
    zone_id: str | None,
    is_saved: bool,
    included_pnu_set: set[str] | None = None,
) -> MapZoneResponse:
    included_set = included_pnu_set or {item.pnu for item in preview.parcels if item.selected_by_rule}
    included_parcels = [item for item in preview.parcels if item.pnu in included_set]
    summary_values = calculate_summary(preview.parcels, included_pnu_set=included_set)
    building_summary = calculate_zone_building_summary(
        included_parcels,
        metrics_by_pnu=preview.building_metrics_by_pnu,
    )

    parcels = [
        MapZoneParcelItem(
            pnu=item.pnu,
            jibun_address=item.jibun_address,
            road_address=item.road_address,
            land_category_name=item.land_category_name,
            purpose_area_name=item.purpose_area_name,
            geometry_geojson=item.geometry_geojson,
            area_sqm=item.area_sqm,
            overlap_area_sqm=item.overlap_area_sqm,
            price_current=item.price_current,
            price_year=item.price_year,
            estimated_total_price=calculate_estimated_total_price(item.area_sqm, item.price_current),
            geometry_estimated_total_price=calculate_estimated_total_price(item.overlap_area_sqm, item.price_current),
            overlap_ratio=round(item.overlap_ratio, 4),
            centroid_in=item.centroid_in,
            selected_by_rule=item.selected_by_rule,
            inclusion_mode=(
                item.inclusion_mode
                if item.pnu in included_set
                else ("user_excluded" if item.selected_by_rule else item.inclusion_mode)
            ),
            confidence_score=item.confidence_score,
            ai_recommendation=item.ai_recommendation,
            ai_confidence_score=item.ai_confidence_score,
            ai_reason_codes=item.ai_reason_codes or [],
            ai_reason_text=item.ai_reason_text,
            ai_model_version=item.ai_model_version,
            ai_applied=(
                item.pnu in included_set and not item.selected_by_rule and item.ai_recommendation == "included"
            ),
            selection_origin=(
                "rule"
                if item.selected_by_rule and item.pnu in included_set
                else ("ai" if item.pnu in included_set and item.ai_recommendation == "included" else "user")
            ),
            anomaly_codes=item.anomaly_codes or [],
            anomaly_level=item.anomaly_level,
            building_confidence=item.building_confidence,
            household_confidence=item.household_confidence,
            floor_area_ratio_confidence=item.floor_area_ratio_confidence,
            included=item.pnu in included_set,
            counted_in_summary=bool(
                item.pnu in included_set
                and item.price_current is not None
                and item.price_year is not None
                and item.price_year == summary_values["base_year"]
            ),
            lat=item.lat,
            lng=item.lng,
            building_count=item.building_count,
            aged_building_count=item.aged_building_count,
            average_approval_year=item.average_approval_year,
            price_previous=item.price_previous,
            growth_rate=item.growth_rate,
            aged_building_ratio=item.aged_building_ratio,
            site_area_sqm=preview.building_metrics_by_pnu.get(item.pnu).site_area_sqm if item.pnu in preview.building_metrics_by_pnu else None,
            total_floor_area_sqm=item.total_floor_area_sqm,
            floor_area_ratio=item.floor_area_ratio,
            building_coverage_ratio=item.building_coverage_ratio,
            household_count=item.household_count,
            primary_purpose_name=item.primary_purpose_name,
        )
        for item in preview.parcels
    ]
    summary = MapZoneSummary(
        zone_id=zone_id,
        zone_name=preview.zone_name,
        is_saved=is_saved,
        base_year=summary_values["base_year"],
        overlap_threshold=round(preview.threshold, 4),
        zone_area_sqm=round(summary_values["zone_area_sqm"], 2),
        overlap_area_sqm_total=round(summary_values["overlap_area_sqm_total"], 2),
        parcel_count=summary_values["parcel_count"],
        boundary_parcel_count=summary_values["boundary_parcel_count"],
        counted_parcel_count=summary_values["counted_parcel_count"],
        excluded_parcel_count=summary_values["excluded_parcel_count"],
        average_unit_price=calculate_average_unit_price(
            assessed_total_price=summary_values["assessed_total_price"],
            zone_area_sqm=float(summary_values["zone_area_sqm"]),
        ),
        assessed_total_price=summary_values["assessed_total_price"],
        geometry_assessed_total_price=summary_values["geometry_assessed_total_price"],
        algorithm_version=summary_values["algorithm_version"],
        ai_model_version=preview.ai_model_version,
        ai_report_text=preview.ai_report_text,
        ai_recommended_include_count=sum(1 for item in parcels if item.ai_recommendation == "included"),
        ai_uncertain_count=sum(1 for item in parcels if item.ai_recommendation == "uncertain"),
        ai_excluded_count=sum(1 for item in parcels if item.ai_recommendation == "excluded"),
        anomaly_parcel_count=sum(1 for item in parcels if item.anomaly_level and item.anomaly_level != "none"),
        building_data_ready=preview.building_data_ready,
        building_data_message=preview.building_data_message,
        total_building_count=int(building_summary["total_building_count"]),
        aged_building_count=int(building_summary["aged_building_count"]),
        aged_building_ratio=building_summary["aged_building_ratio"],
        average_approval_year=building_summary["average_approval_year"],
        total_floor_area_sqm=building_summary["total_floor_area_sqm"],
        total_site_area_sqm=building_summary["total_site_area_sqm"],
        average_floor_area_ratio=building_summary["average_floor_area_ratio"],
        undersized_parcel_count=int(building_summary["undersized_parcel_count"]),
        undersized_parcel_ratio=building_summary["undersized_parcel_ratio"],
        created_at=to_iso(preview.generated_at),
        updated_at=to_iso(preview.generated_at),
    )
    return MapZoneResponse(
        summary=summary,
        coordinates=[MapCoordinate(lat=lat, lng=lng) for lng, lat in preview.coordinates[:-1]],
        parcels=parcels,
    )


def _build_saved_zone_ai_report(parcels: list[MapZoneParcelItem]) -> str | None:
    if not parcels:
        return None
    include_count = sum(1 for item in parcels if item.ai_recommendation == "included")
    uncertain_count = sum(1 for item in parcels if item.ai_recommendation == "uncertain")
    anomaly_count = sum(1 for item in parcels if item.anomaly_level and item.anomaly_level != "none")
    return (
        f"AI가 {len(parcels)}개 필지를 검토했습니다. 추천 포함 {include_count}건, "
        f"경계 검토 {uncertain_count}건, 이상치 검토 {anomaly_count}건입니다."
    )
