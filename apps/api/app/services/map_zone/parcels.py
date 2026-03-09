from __future__ import annotations

import json
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.map_service import _fetch_land_characteristics_latest, _get_redis_client, _to_text_or_none
from app.services.vworld_service import call_vworld_json

from .domain import VWorldParcelFeature, ZoneParcelComputed
from .geometry import is_postgres
from .summary import to_float, to_int

PNU_PATTERN = re.compile(r"^\d{19}$")


def fetch_vworld_parcel_features(bbox: tuple[float, float, float, float]) -> dict[str, VWorldParcelFeature]:
    return _fetch_vworld_parcel_features_recursive(bbox, depth=0)


def _fetch_vworld_parcel_features_recursive(
    bbox: tuple[float, float, float, float],
    *,
    depth: int,
) -> dict[str, VWorldParcelFeature]:
    response, total_pages = _fetch_vworld_parcel_feature_page(bbox, page=1)
    max_pages = max(1, settings.map_zone_vworld_max_pages)
    if total_pages <= max_pages:
        return _collect_vworld_parcel_feature_pages(bbox, first_response=response, total_pages=total_pages)

    max_depth = max(0, int(settings.map_zone_bbox_split_max_depth))
    if depth >= max_depth or _is_bbox_too_small(bbox):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "ZONE_TOO_MANY_FEATURE_PAGES",
                "message": (
                    f"구역 범위의 필지 수가 많아 단일 분석 한도를 초과했습니다. "
                    f"구역을 더 작게 나눠 조회해 주세요. (pages={total_pages})"
                ),
            },
        )

    feature_map: dict[str, VWorldParcelFeature] = {}
    for child_bbox in _split_bbox_into_quadrants(bbox):
        if _bbox_has_no_area(child_bbox):
            continue
        child_features = _fetch_vworld_parcel_features_recursive(child_bbox, depth=depth + 1)
        _merge_vworld_feature_maps(feature_map, child_features)
    return feature_map


def _collect_vworld_parcel_feature_pages(
    bbox: tuple[float, float, float, float],
    *,
    first_response: dict[str, Any],
    total_pages: int,
) -> dict[str, VWorldParcelFeature]:
    feature_map: dict[str, VWorldParcelFeature] = {}
    _merge_vworld_feature_maps(feature_map, _parse_vworld_feature_response(first_response))

    for current_page in range(2, total_pages + 1):
        response, _ = _fetch_vworld_parcel_feature_page(bbox, page=current_page)
        _merge_vworld_feature_maps(feature_map, _parse_vworld_feature_response(response))
    return feature_map


def _fetch_vworld_parcel_feature_page(
    bbox: tuple[float, float, float, float],
    *,
    page: int,
) -> tuple[dict[str, Any], int]:
    min_lng, min_lat, max_lng, max_lat = bbox
    geom_filter = f"BOX({min_lng:.12f},{min_lat:.12f},{max_lng:.12f},{max_lat:.12f})"
    page_size = max(100, min(settings.map_zone_vworld_page_size, 1000))

    payload = call_vworld_json(
        "/req/data",
        {
            "service": "data",
            "request": "GetFeature",
            "data": "LP_PA_CBND_BUBUN",
            "version": "2.0",
            "format": "json",
            "geomFilter": geom_filter,
            "size": str(page_size),
            "page": str(page),
        },
    )

    response = payload.get("response", {})
    status_text = str(response.get("status", "")).upper()
    if status_text != "OK":
        error_text = ""
        error = response.get("error")
        if isinstance(error, dict):
            error_text = str(error.get("text", "")).strip()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "VWORLD_ZONE_FEATURE_FAILED", "message": error_text or "지적도 데이터를 불러오지 못했습니다."},
        )

    page_info = response.get("page", {}) if isinstance(response.get("page"), dict) else {}
    total_pages = int(page_info.get("total", 1) or 1)
    return response, total_pages


def _parse_vworld_feature_response(response: dict[str, Any]) -> dict[str, VWorldParcelFeature]:
    feature_map: dict[str, VWorldParcelFeature] = {}
    for item in _extract_feature_list(response):
        feature = _parse_vworld_feature(item)
        if feature is None:
            continue
        prev = feature_map.get(feature.pnu)
        if prev is None or (feature.price_year or "") >= (prev.price_year or ""):
            feature_map[feature.pnu] = feature
    return feature_map


def _merge_vworld_feature_maps(
    target: dict[str, VWorldParcelFeature],
    incoming: dict[str, VWorldParcelFeature],
) -> None:
    for pnu, feature in incoming.items():
        prev = target.get(pnu)
        if prev is None or (feature.price_year or "") >= (prev.price_year or ""):
            target[pnu] = feature


def _split_bbox_into_quadrants(
    bbox: tuple[float, float, float, float],
) -> list[tuple[float, float, float, float]]:
    min_lng, min_lat, max_lng, max_lat = bbox
    mid_lng = (min_lng + max_lng) / 2
    mid_lat = (min_lat + max_lat) / 2
    return [
        (min_lng, min_lat, mid_lng, mid_lat),
        (mid_lng, min_lat, max_lng, mid_lat),
        (min_lng, mid_lat, mid_lng, max_lat),
        (mid_lng, mid_lat, max_lng, max_lat),
    ]


def _bbox_has_no_area(bbox: tuple[float, float, float, float]) -> bool:
    min_lng, min_lat, max_lng, max_lat = bbox
    return max_lng <= min_lng or max_lat <= min_lat


def _is_bbox_too_small(bbox: tuple[float, float, float, float]) -> bool:
    min_lng, min_lat, max_lng, max_lat = bbox
    return abs(max_lng - min_lng) < 1e-6 or abs(max_lat - min_lat) < 1e-6


def _extract_feature_list(response: dict[str, Any]) -> list[dict[str, Any]]:
    result = response.get("result", {})
    if not isinstance(result, dict):
        return []
    collection = result.get("featureCollection", {})
    if not isinstance(collection, dict):
        return []
    features = collection.get("features")
    if not isinstance(features, list):
        return []
    return [item for item in features if isinstance(item, dict)]


def _parse_vworld_feature(raw: dict[str, Any]) -> VWorldParcelFeature | None:
    properties = raw.get("properties", {})
    geometry = raw.get("geometry")
    if not isinstance(properties, dict) or not isinstance(geometry, dict):
        return None

    pnu = str(properties.get("pnu") or "").strip()
    if not PNU_PATTERN.fullmatch(pnu):
        return None

    try:
        geometry_json = json.dumps(geometry, ensure_ascii=False)
    except (TypeError, ValueError):
        return None

    address = str(properties.get("addr") or "").strip()
    price_current = to_int(properties.get("jiga"))
    price_year = str(properties.get("gosi_year") or "").strip()
    if not re.fullmatch(r"\d{4}", price_year):
        price_year = None

    return VWorldParcelFeature(
        pnu=pnu,
        geometry_json=geometry_json,
        address=address,
        price_current=price_current,
        price_year=price_year,
    )


def upsert_parcel_geometries(db: Session, features: list[VWorldParcelFeature]) -> None:
    if not features:
        return

    now = datetime.now(timezone.utc)
    feature_payload = json.dumps(
        [
            {
                "id": str(uuid.uuid4()),
                "pnu": item.pnu,
                "geometry_json": item.geometry_json,
                "price_current": item.price_current,
            }
            for item in features
        ],
        ensure_ascii=False,
    )
    db.execute(
        text(
            """
            WITH src AS (
              SELECT
                item->>'id' AS id,
                item->>'pnu' AS pnu,
                item->>'geometry_json' AS geometry_json,
                NULLIF(item->>'price_current', '')::BIGINT AS price_current
              FROM jsonb_array_elements(CAST(:feature_payload AS JSONB)) AS item
            ),
            geom_data AS (
              SELECT
                id,
                pnu,
                price_current,
                ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(geometry_json), 4326)) AS geom
              FROM src
            ),
            prepared AS (
              SELECT
                id,
                pnu,
                price_current,
                ST_Y(ST_Centroid(geom)) AS lat,
                ST_X(ST_Centroid(geom)) AS lng,
                ST_Area(geom::geography) AS area,
                geom
              FROM geom_data
            )
            INSERT INTO parcels (
              id, pnu, lat, lng, area, price_current, price_previous, updated_at, geog, geom
            )
            SELECT
              id,
              pnu,
              lat,
              lng,
              area,
              price_current,
              NULL,
              :updated_at,
              ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
              geom
            FROM prepared
            ON CONFLICT (pnu) DO UPDATE
            SET
              lat = EXCLUDED.lat,
              lng = EXCLUDED.lng,
              area = COALESCE(EXCLUDED.area, parcels.area),
              price_current = COALESCE(EXCLUDED.price_current, parcels.price_current),
              updated_at = EXCLUDED.updated_at,
              geog = EXCLUDED.geog,
              geom = EXCLUDED.geom
            """
        ),
        {
            "feature_payload": feature_payload,
            "updated_at": now,
        },
    )
    db.flush()


def query_overlapped_parcels(
    db: Session,
    *,
    zone_wkt: str,
    threshold: float,
    pnu_list: list[str],
) -> list[dict[str, Any]]:
    if not pnu_list:
        return []

    bind_params: dict[str, Any] = {"zone_wkt": zone_wkt, "threshold": threshold}
    placeholders: list[str] = []
    for idx, pnu in enumerate(pnu_list):
        key = f"pnu_{idx}"
        bind_params[key] = pnu
        placeholders.append(f":{key}")

    if is_postgres(db):
        timeout_ms = max(1000, int(settings.map_zone_query_timeout_ms))
        db.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))

    query = f"""
        WITH zone AS (
          SELECT ST_GeomFromText(:zone_wkt, 4326) AS geom
        ),
        candidates AS (
          SELECT
            p.pnu,
            p.lat,
            p.lng,
            COALESCE(p.area, ST_Area(p.geom::geography)) AS area_sqm,
            ST_AsGeoJSON(p.geom) AS geometry_geojson,
            p.geom AS geom,
            ST_Area(ST_Intersection(p.geom, z.geom)::geography) AS overlap_area_sqm,
            ST_Area(ST_Intersection(p.geom, z.geom)::geography) / NULLIF(ST_Area(p.geom::geography), 0) AS overlap_ratio,
            CASE WHEN ST_Contains(z.geom, ST_Centroid(p.geom)) THEN TRUE ELSE FALSE END AS centroid_in
          FROM parcels p
          CROSS JOIN zone z
          WHERE p.geom IS NOT NULL
            AND p.pnu IN ({", ".join(placeholders)})
            AND ST_Intersects(p.geom, z.geom)
        ),
        anchors AS (
          SELECT pnu, geom
          FROM candidates
          WHERE overlap_ratio >= :threshold OR centroid_in = TRUE
        ),
        scored AS (
          SELECT
            c.pnu,
            c.lat,
            c.lng,
            c.area_sqm,
            c.geometry_geojson,
            c.overlap_area_sqm,
            c.overlap_ratio,
            c.centroid_in,
            CASE
              WHEN EXISTS (
                SELECT 1
                FROM anchors a
                WHERE a.pnu <> c.pnu
                  AND ST_Intersects(a.geom, c.geom)
              ) THEN TRUE
              ELSE FALSE
            END AS adjacency_bonus
          FROM candidates c
        )
        SELECT
          pnu,
          lat,
          lng,
          area_sqm,
          geometry_geojson,
          overlap_area_sqm,
          overlap_ratio,
          centroid_in,
          adjacency_bonus
        FROM scored
        ORDER BY overlap_ratio DESC, pnu ASC
    """
    rows = db.execute(text(query), bind_params).mappings().all()
    return [dict(row) for row in rows]


def compose_zone_parcels(
    rows: list[dict[str, Any]],
    feature_map: dict[str, VWorldParcelFeature],
    land_metadata_map: dict[str, dict[str, str | None]],
    *,
    threshold: float,
) -> list[ZoneParcelComputed]:
    parcels: list[ZoneParcelComputed] = []
    for row in rows:
        pnu = str(row.get("pnu") or "").strip()
        if not pnu:
            continue
        feature = feature_map.get(pnu)
        land_metadata = land_metadata_map.get(pnu, {})
        area_sqm = float(row.get("area_sqm") or 0.0)
        overlap_area_sqm = float(row.get("overlap_area_sqm") or 0.0)
        overlap_ratio = float(row.get("overlap_ratio") or 0.0)
        centroid_in = bool(row.get("centroid_in"))
        adjacency_bonus = bool(row.get("adjacency_bonus"))
        confidence_score, selected_by_rule, inclusion_mode = _classify_zone_parcel(
            overlap_ratio=overlap_ratio,
            centroid_in=centroid_in,
            adjacency_bonus=adjacency_bonus,
            threshold=threshold,
        )
        parcels.append(
            ZoneParcelComputed(
                pnu=pnu,
                lat=to_float(row.get("lat")),
                lng=to_float(row.get("lng")),
                area_sqm=round(max(0.0, area_sqm), 2),
                overlap_area_sqm=round(max(0.0, overlap_area_sqm), 2),
                overlap_ratio=round(overlap_ratio, 4),
                centroid_in=centroid_in,
                adjacency_bonus=adjacency_bonus,
                selected_by_rule=selected_by_rule,
                inclusion_mode=inclusion_mode,
                confidence_score=confidence_score,
                price_current=feature.price_current if feature else None,
                price_year=feature.price_year if feature else None,
                jibun_address=(feature.address if feature else "") or pnu,
                road_address="",
                land_category_name=land_metadata.get("land_category_name"),
                purpose_area_name=land_metadata.get("purpose_area_name"),
                geometry_geojson=_to_text_or_none(row.get("geometry_geojson")),
            )
        )
    return parcels


def _classify_zone_parcel(
    *,
    overlap_ratio: float,
    centroid_in: bool,
    adjacency_bonus: bool,
    threshold: float,
) -> tuple[float, bool, str]:
    confidence_score = round(
        min(
            1.0,
            (0.6 * max(0.0, min(overlap_ratio, 1.0)))
            + (0.3 if centroid_in else 0.0)
            + (0.1 if adjacency_bonus else 0.0),
        ),
        4,
    )
    if overlap_ratio >= threshold:
        return confidence_score, True, "rule_overlap"
    if confidence_score >= 0.8:
        return confidence_score, True, "score_auto"
    if confidence_score >= 0.5:
        return confidence_score, False, "boundary_candidate"
    return confidence_score, False, "excluded"


def fetch_saved_zone_parcel_metadata(db: Session, pnu_list: list[str]) -> dict[str, str]:
    unique_pnu_list = [pnu for pnu in dict.fromkeys(pnu_list) if pnu]
    if not unique_pnu_list:
        return {}

    bind_params: dict[str, Any] = {}
    placeholders: list[str] = []
    for idx, pnu in enumerate(unique_pnu_list):
        key = f"meta_pnu_{idx}"
        bind_params[key] = pnu
        placeholders.append(f":{key}")

    rows = db.execute(
        text(
            f"""
            SELECT pnu, ST_AsGeoJSON(geom) AS geometry_geojson
            FROM parcels
            WHERE geom IS NOT NULL
              AND pnu IN ({", ".join(placeholders)})
            """
        ),
        bind_params,
    ).mappings().all()
    return {
        str(row.get("pnu") or "").strip(): str(row.get("geometry_geojson") or "").strip()
        for row in rows
        if row.get("pnu") and row.get("geometry_geojson")
    }


def fetch_zone_land_metadata(pnu_list: list[str]) -> dict[str, dict[str, str | None]]:
    metadata_map: dict[str, dict[str, str | None]] = {}
    missing_pnu_list: list[str] = []
    redis_client = _get_redis_client()

    for pnu in dict.fromkeys(pnu_list):
        if not pnu:
            continue
        cached = _load_zone_land_metadata_from_cache(redis_client, pnu)
        if cached is not None:
            metadata_map[pnu] = cached
            continue
        missing_pnu_list.append(pnu)

    sync_limit = max(0, int(settings.map_zone_land_metadata_sync_limit))
    if sync_limit == 0 or not missing_pnu_list:
        return metadata_map

    fetch_targets = missing_pnu_list[:sync_limit]
    worker_count = max(1, min(int(settings.map_zone_land_metadata_workers), len(fetch_targets)))

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {executor.submit(_fetch_single_zone_land_metadata, pnu): pnu for pnu in fetch_targets}
        for future in as_completed(future_map):
            pnu = future_map[future]
            try:
                metadata = future.result()
            except Exception:
                metadata = {"land_category_name": None, "purpose_area_name": None}
            metadata_map[pnu] = metadata
            _store_zone_land_metadata_in_cache(redis_client, pnu, metadata)

    return metadata_map


def _fetch_single_zone_land_metadata(pnu: str) -> dict[str, str | None]:
    details = _fetch_land_characteristics_latest(pnu) or {}
    return {
        "land_category_name": _to_text_or_none(details.get("lndcgrCodeNm")),
        "purpose_area_name": _to_text_or_none(details.get("prposAreaNm") or details.get("prposArea1Nm")),
    }


def _land_metadata_cache_key(pnu: str) -> str:
    return f"map:zone-land-meta:{pnu}"


def _load_zone_land_metadata_from_cache(
    redis_client: Any,
    pnu: str,
) -> dict[str, str | None] | None:
    if redis_client is None:
        return None
    try:
        cached = redis_client.get(_land_metadata_cache_key(pnu))
    except Exception:
        return None
    if not cached:
        return None
    try:
        payload = json.loads(cached)
    except (TypeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    return {
        "land_category_name": _to_text_or_none(payload.get("land_category_name")),
        "purpose_area_name": _to_text_or_none(payload.get("purpose_area_name")),
    }


def _store_zone_land_metadata_in_cache(
    redis_client: Any,
    pnu: str,
    metadata: dict[str, str | None],
) -> None:
    if redis_client is None:
        return
    try:
        redis_client.setex(
            _land_metadata_cache_key(pnu),
            settings.map_price_cache_ttl_seconds,
            json.dumps(metadata, ensure_ascii=False),
        )
    except Exception:
        return
