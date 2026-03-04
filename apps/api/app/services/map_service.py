from __future__ import annotations

import csv
import io
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.land import LandResultRow
from app.schemas.map import MapClickRequest, MapLookupResponse
from app.services.vworld_service import call_vworld_json, compose_pnu, fetch_individual_land_price_rows, parse_level5_jibun

try:
    from redis import Redis
    from redis.exceptions import RedisError

    _REDIS_AVAILABLE = True
except ModuleNotFoundError:  # pragma: no cover - optional dependency in local/dev
    Redis = Any  # type: ignore[assignment]

    class RedisError(Exception):
        pass

    _REDIS_AVAILABLE = False

_PRICE_DIGITS = re.compile(r"[^0-9]")
_REDIS_CLIENT: Redis | None = None
_REDIS_DISABLED = False


def lookup_map_by_click(db: Session, payload: MapClickRequest) -> MapLookupResponse:
    _validate_lat_lng(payload.lat, payload.lng)

    pnu_data = _resolve_pnu_with_cache(payload.lat, payload.lng)
    pnu = pnu_data["pnu"]
    address_summary = pnu_data["address_summary"]

    cached = _find_cached_parcel(db, pnu)
    rows: list[LandResultRow] = []
    cache_hit = False

    if cached and _is_fresh(cached.get("updated_at")):
        area = _to_float(cached.get("area"))
        price_current = _to_int(cached.get("price_current"))
        price_previous = _to_int(cached.get("price_previous"))
        cache_hit = True
    else:
        rows = fetch_individual_land_price_rows(pnu)
        price_current = _parse_price(rows[0].개별공시지가) if rows else None
        price_previous = _parse_price(rows[1].개별공시지가) if len(rows) > 1 else None
        area = _fetch_parcel_area(pnu)
        _upsert_parcel_snapshot(
            db=db,
            pnu=pnu,
            lat=payload.lat,
            lng=payload.lng,
            area=area,
            price_current=price_current,
            price_previous=price_previous,
        )

    nearby_avg = _fetch_nearby_avg_price(db, pnu, payload.lat, payload.lng, settings.map_nearby_radius_m)
    growth_rate = _calculate_growth_rate(price_current, price_previous)
    estimated_total_price = _calculate_total_price(area, price_current)

    return MapLookupResponse(
        lat=payload.lat,
        lng=payload.lng,
        pnu=pnu,
        address_summary=address_summary,
        area=area,
        price_current=price_current,
        price_previous=price_previous,
        growth_rate=growth_rate,
        estimated_total_price=estimated_total_price,
        nearby_avg_price=nearby_avg,
        nearby_radius_m=settings.map_nearby_radius_m,
        cache_hit=cache_hit,
        rows=rows,
    )


def export_map_csv(db: Session, pnu: str) -> Response:
    row = db.execute(
        text(
            """
            SELECT pnu, area, price_current, price_previous
            FROM parcels
            WHERE pnu = :pnu
            """
        ),
        {"pnu": pnu.strip()},
    ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PARCEL_NOT_FOUND", "message": "요청한 PNU 데이터가 없습니다."},
        )

    area = _to_float(row.get("area"))
    current_price = _to_int(row.get("price_current"))
    previous_price = _to_int(row.get("price_previous"))
    growth_rate = _calculate_growth_rate(current_price, previous_price)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["pnu", "area", "current_price", "previous_price", "growth_rate"])
    writer.writerow(
        [
            row.get("pnu") or "",
            _format_csv_float(area),
            current_price or "",
            previous_price or "",
            _format_csv_float(growth_rate),
        ]
    )

    filename = f"parcel_{pnu}.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _resolve_pnu_with_cache(lat: float, lng: float) -> dict[str, str]:
    cache_key = _pnu_cache_key(lat, lng)
    redis_client = _get_redis_client()

    if redis_client is not None:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                payload = json.loads(cached)
                if isinstance(payload, dict):
                    pnu = str(payload.get("pnu", "")).strip()
                    summary = str(payload.get("address_summary", "")).strip()
                    if pnu:
                        return {"pnu": pnu, "address_summary": summary}
        except (RedisError, json.JSONDecodeError, TypeError, ValueError):
            pass

    resolved = _resolve_pnu_from_vworld(lat, lng)
    if redis_client is not None:
        try:
            redis_client.setex(cache_key, settings.redis_pnu_ttl_seconds, json.dumps(resolved, ensure_ascii=False))
        except RedisError:
            pass
    return resolved


def _resolve_pnu_from_vworld(lat: float, lng: float) -> dict[str, str]:
    payload = call_vworld_json(
        "/req/address",
        {
            "service": "address",
            "request": "getaddress",
            "version": "2.0",
            "crs": "epsg:4326",
            "point": f"{lng},{lat}",
            "format": "json",
            "type": "parcel",
            "simple": "false",
        },
    )

    response = payload.get("response", {})
    if response.get("status") != "OK":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MAP_REVERSE_GEOCODE_FAILED", "message": "좌표를 PNU로 변환하지 못했습니다."},
        )

    results = response.get("result") or []
    if not isinstance(results, list) or not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "MAP_PARCEL_NOT_FOUND", "message": "해당 좌표의 지번 정보를 찾지 못했습니다."},
        )

    first = results[0]
    structure = first.get("structure", {}) if isinstance(first, dict) else {}
    ld_code = str(structure.get("level4LC", "")).strip()
    level5 = str(structure.get("level5", "")).strip()
    if not ld_code or not level5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MAP_PNU_DATA_INVALID", "message": "PNU 생성에 필요한 정보가 누락되었습니다."},
        )

    parsed = parse_level5_jibun(level5)
    pnu = compose_pnu(
        ld_code=ld_code,
        is_san=parsed["is_san"],
        main_no=str(parsed["main_no"]),
        sub_no=str(parsed["sub_no"]),
    )
    address_summary = str(first.get("text", "")).strip() if isinstance(first, dict) else ""
    if not address_summary:
        level1 = str(structure.get("level1", "")).strip()
        level2 = str(structure.get("level2", "")).strip()
        level3 = str(structure.get("level3", "")).strip()
        level4 = str(structure.get("level4", "")).strip()
        address_summary = " ".join(part for part in [level1, level2, level3, level4, level5] if part)

    return {"pnu": pnu, "address_summary": address_summary}


def _find_cached_parcel(db: Session, pnu: str) -> dict[str, Any] | None:
    row = db.execute(
        text(
            """
            SELECT pnu, area, price_current, price_previous, updated_at
            FROM parcels
            WHERE pnu = :pnu
            """
        ),
        {"pnu": pnu},
    ).mappings().first()
    return dict(row) if row else None


def _upsert_parcel_snapshot(
    db: Session,
    pnu: str,
    lat: float,
    lng: float,
    area: float | None,
    price_current: int | None,
    price_previous: int | None,
) -> None:
    now = datetime.now(timezone.utc)
    update_result = db.execute(
        text(
            """
            UPDATE parcels
            SET lat = :lat,
                lng = :lng,
                area = :area,
                price_current = :price_current,
                price_previous = :price_previous,
                updated_at = :updated_at
            WHERE pnu = :pnu
            """
        ),
        {
            "pnu": pnu,
            "lat": lat,
            "lng": lng,
            "area": area,
            "price_current": price_current,
            "price_previous": price_previous,
            "updated_at": now,
        },
    )

    if update_result.rowcount == 0:
        db.execute(
            text(
                """
                INSERT INTO parcels (id, pnu, lat, lng, area, price_current, price_previous, updated_at)
                VALUES (:id, :pnu, :lat, :lng, :area, :price_current, :price_previous, :updated_at)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "pnu": pnu,
                "lat": lat,
                "lng": lng,
                "area": area,
                "price_current": price_current,
                "price_previous": price_previous,
                "updated_at": now,
            },
        )

    if _is_postgres(db):
        db.execute(
            text(
                """
                UPDATE parcels
                SET geog = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
                WHERE pnu = :pnu
                """
            ),
            {"pnu": pnu, "lat": lat, "lng": lng},
        )

    db.commit()


def _fetch_nearby_avg_price(db: Session, pnu: str, lat: float, lng: float, radius_m: int) -> int | None:
    if not _is_postgres(db):
        return None

    row = db.execute(
        text(
            """
            SELECT ROUND(AVG(price_current))::BIGINT AS nearby_avg
            FROM parcels
            WHERE pnu <> :pnu
              AND price_current IS NOT NULL
              AND geog IS NOT NULL
              AND ST_DWithin(
                    geog,
                    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
                    :radius_m
              )
            """
        ),
        {"pnu": pnu, "lat": lat, "lng": lng, "radius_m": radius_m},
    ).mappings().first()

    if not row:
        return None
    return _to_int(row.get("nearby_avg"))


def _fetch_parcel_area(pnu: str) -> float | None:
    try:
        payload = call_vworld_json(
            "/ned/data/getParcelLandAttr",
            {
                "pnu": pnu,
                "format": "json",
                "numOfRows": "10",
                "pageNo": "1",
            },
        )
    except HTTPException:
        return None

    root_candidates: list[Any] = [
        payload.get("parcelLandAttrs"),
        payload.get("parcelLandAttr"),
        payload.get("parcelLands"),
        payload.get("parcelLand"),
        payload,
    ]
    field_candidates: list[Any] = []
    for root in root_candidates:
        if isinstance(root, dict):
            field_candidates.append(root.get("field"))
            field_candidates.append(root.get("result"))
            field_candidates.append(root.get("items"))

    for candidate in field_candidates:
        area = _extract_area_from_candidate(candidate)
        if area is not None:
            return area

    return _extract_area_from_candidate(payload)


def _extract_area_from_candidate(value: Any) -> float | None:
    if isinstance(value, list):
        for item in value:
            area = _extract_area_from_candidate(item)
            if area is not None:
                return area
        return None

    if not isinstance(value, dict):
        return None

    preferred_keys = (
        "lndpclAr",
        "lndAr",
        "landAr",
        "parcelAr",
        "parcelArea",
        "area",
        "ladAr",
        "lndcgrAr",
    )
    for key in preferred_keys:
        if key in value:
            parsed = _to_float(value.get(key))
            if parsed is not None and parsed > 0:
                return parsed

    for raw in value.values():
        parsed = _to_float(raw)
        if parsed is not None and 1 <= parsed <= 10_000_000:
            return parsed
    return None


def _validate_lat_lng(lat: float, lng: float) -> None:
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_COORDINATE", "message": "위도/경도 범위를 확인해 주세요."},
        )


def _parse_price(value: str | None) -> int | None:
    if not value:
        return None
    digits = _PRICE_DIGITS.sub("", value)
    if not digits:
        return None
    try:
        return int(digits)
    except ValueError:
        return None


def _calculate_growth_rate(current: int | None, previous: int | None) -> float | None:
    if current is None or previous is None or previous <= 0:
        return None
    return round(((current - previous) / previous) * 100, 2)


def _calculate_total_price(area: float | None, current: int | None) -> int | None:
    if area is None or current is None:
        return None
    return int(round(area * current))


def _is_fresh(updated_at: Any) -> bool:
    parsed = _to_datetime(updated_at)
    if parsed is None:
        return False
    return datetime.now(timezone.utc) - parsed <= timedelta(seconds=settings.map_price_cache_ttl_seconds)


def _to_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        text_value = value.strip().replace("Z", "+00:00")
        if not text_value:
            return None
        try:
            parsed = datetime.fromisoformat(text_value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        value = value.replace(",", "")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_csv_float(value: float | None) -> str:
    if value is None:
        return ""
    if value.is_integer():
        return str(int(value))
    return f"{value:.2f}"


def _pnu_cache_key(lat: float, lng: float) -> str:
    return f"map:pnu:{lat:.6f}:{lng:.6f}"


def _is_postgres(db: Session) -> bool:
    return db.bind is not None and db.bind.dialect.name == "postgresql"


def _get_redis_client() -> Redis | None:
    global _REDIS_CLIENT, _REDIS_DISABLED
    if not _REDIS_AVAILABLE:
        return None
    if _REDIS_DISABLED:
        return None
    if _REDIS_CLIENT is not None:
        return _REDIS_CLIENT
    if not settings.redis_url.strip():
        return None

    try:
        client = Redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=2.0)
        client.ping()
        _REDIS_CLIENT = client
        return _REDIS_CLIENT
    except RedisError:
        _REDIS_DISABLED = True
        return None
