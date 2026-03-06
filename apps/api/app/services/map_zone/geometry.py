from __future__ import annotations

import re

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.map import MapCoordinate

SAFE_ZONE_NAME_PATTERN = re.compile(r"^[0-9A-Za-z가-힣\s\-_().]+$")


def normalize_zone_name(zone_name: str) -> str:
    normalized = zone_name.strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ZONE_NAME", "message": "구역 이름을 입력해 주세요."},
        )
    if not SAFE_ZONE_NAME_PATTERN.fullmatch(normalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_ZONE_NAME", "message": "구역 이름에 허용되지 않는 문자가 포함되어 있습니다."},
        )
    return normalized


def resolve_overlap_threshold(requested: float | None) -> float:
    threshold = settings.map_zone_overlap_threshold if requested is None else requested
    if threshold <= 0 or threshold > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_OVERLAP_THRESHOLD", "message": "포함 임계치는 0 초과 1 이하 값이어야 합니다."},
        )
    return float(threshold)


def normalize_polygon_coordinates(coords: list[MapCoordinate]) -> list[tuple[float, float]]:
    max_vertices = max(3, settings.map_zone_max_vertices)
    if len(coords) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ZONE_TOO_FEW_POINTS", "message": "구역 좌표는 최소 3개 이상 필요합니다."},
        )
    if len(coords) > max_vertices:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ZONE_TOO_MANY_POINTS", "message": f"구역 꼭짓점은 최대 {max_vertices}개까지 허용됩니다."},
        )

    points: list[tuple[float, float]] = []
    for item in coords:
        lat = float(item.lat)
        lng = float(item.lng)
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_COORDINATE", "message": "위도/경도 범위를 확인해 주세요."},
            )
        points.append((lng, lat))

    unique_points = {(round(lng, 10), round(lat, 10)) for lng, lat in points}
    if len(unique_points) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ZONE_TOO_FEW_UNIQUE_POINTS", "message": "서로 다른 좌표 3개 이상이 필요합니다."},
        )

    first = points[0]
    last = points[-1]
    if abs(first[0] - last[0]) > 1e-9 or abs(first[1] - last[1]) > 1e-9:
        points.append(first)
    return points


def coordinates_to_wkt(coords: list[tuple[float, float]]) -> str:
    serialized = ", ".join(f"{lng:.12f} {lat:.12f}" for lng, lat in coords)
    return f"POLYGON(({serialized}))"


def calculate_bbox(coords: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    lng_values = [lng for lng, _ in coords]
    lat_values = [lat for _, lat in coords]
    return (min(lng_values), min(lat_values), max(lng_values), max(lat_values))


def calculate_zone_area(db: Session, zone_wkt: str) -> float:
    row = db.execute(
        text(
            """
            SELECT ST_Area(ST_GeogFromText(:zone_wkt)) AS area_sqm
            """
        ),
        {"zone_wkt": zone_wkt},
    ).mappings().first()
    area = float(row["area_sqm"]) if row and row.get("area_sqm") is not None else 0.0
    return max(0.0, area)


def validate_zone_geometry(db: Session, zone_wkt: str) -> None:
    row = db.execute(
        text(
            """
            SELECT
              ST_IsValid(geom) AS is_valid,
              ST_IsValidReason(geom) AS reason
            FROM (SELECT ST_GeomFromText(:zone_wkt, 4326) AS geom) AS src
            """
        ),
        {"zone_wkt": zone_wkt},
    ).mappings().first()
    if not row or bool(row.get("is_valid")):
        return
    reason = str(row.get("reason") or "유효하지 않은 폴리곤입니다.")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"code": "INVALID_ZONE_GEOMETRY", "message": f"유효하지 않은 폴리곤입니다: {reason}"},
    )


def is_postgres(db: Session) -> bool:
    return db.bind is not None and db.bind.dialect.name == "postgresql"


def require_postgres(db: Session) -> None:
    if not is_postgres(db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "POSTGIS_REQUIRED", "message": "구역조회 기능은 PostGIS(PostgreSQL) 환경에서만 지원됩니다."},
        )


def zone_wkt_to_coordinates(zone_wkt: str) -> list[MapCoordinate]:
    text_value = (zone_wkt or "").strip()
    if not text_value.upper().startswith("POLYGON((") or not text_value.endswith("))"):
        return []

    serialized = text_value[len("POLYGON((") : -2]
    coordinates: list[MapCoordinate] = []
    for chunk in serialized.split(","):
        parts = chunk.strip().split()
        if len(parts) != 2:
            continue
        try:
            lng = float(parts[0])
            lat = float(parts[1])
        except ValueError:
            continue
        coordinates.append(MapCoordinate(lat=lat, lng=lng))

    if len(coordinates) >= 2:
        first = coordinates[0]
        last = coordinates[-1]
        if abs(first.lat - last.lat) < 1e-9 and abs(first.lng - last.lng) < 1e-9:
            coordinates = coordinates[:-1]
    return coordinates
