from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session
from urllib3.util.retry import Retry

from app.core.config import settings
from app.models.building_register_cache import BuildingRegisterCache

_BUILDING_SESSION: requests.Session | None = None

_RESIDENTIAL_KEYWORDS = ("주택", "아파트", "다세대", "연립", "다가구", "공동주택", "오피스텔", "기숙사")


@dataclass
class BuildingRegisterMetrics:
    pnu: str
    has_building_register: bool = False
    building_count: int = 0
    aged_building_count: int = 0
    residential_building_count: int = 0
    approval_year_sum: int = 0
    approval_year_count: int = 0
    average_approval_year: int | None = None
    total_floor_area_sqm: float | None = None
    site_area_sqm: float | None = None
    floor_area_ratio: float | None = None
    primary_purpose_name: str | None = None


@dataclass
class BuildingRegisterBatchResult:
    metrics_by_pnu: dict[str, BuildingRegisterMetrics]
    ready: bool
    message: str | None


def fetch_building_register_metrics_batch(
    db: Session,
    *,
    parcel_area_by_pnu: dict[str, float],
) -> BuildingRegisterBatchResult:
    unique_pnu_list = [pnu for pnu in dict.fromkeys(parcel_area_by_pnu.keys()) if pnu]
    if not unique_pnu_list:
        return BuildingRegisterBatchResult(metrics_by_pnu={}, ready=True, message=None)

    if not _is_building_api_configured():
        return BuildingRegisterBatchResult(
            metrics_by_pnu={pnu: BuildingRegisterMetrics(pnu=pnu) for pnu in unique_pnu_list},
            ready=False,
            message="건축물대장 API 키가 설정되지 않아 노후도/용적률 분석을 생략했습니다.",
        )

    now = datetime.now(timezone.utc)
    freshness_cutoff = now - timedelta(hours=max(1, settings.map_zone_building_cache_ttl_hours))
    try:
        cache_rows = (
            db.query(BuildingRegisterCache)
            .filter(
                BuildingRegisterCache.pnu.in_(unique_pnu_list),
                BuildingRegisterCache.synced_at >= freshness_cutoff,
            )
            .all()
        )
    except (ProgrammingError, OperationalError):
        db.rollback()
        cache_rows = []
    metrics_by_pnu = {row.pnu: _cache_row_to_metrics(row) for row in cache_rows}

    missing_pnu_list = [pnu for pnu in unique_pnu_list if pnu not in metrics_by_pnu]
    if not missing_pnu_list:
        return BuildingRegisterBatchResult(metrics_by_pnu=metrics_by_pnu, ready=True, message=None)

    errors: list[str] = []
    fetched_rows: list[BuildingRegisterCache] = []
    max_workers = max(1, min(settings.map_zone_building_workers, len(missing_pnu_list)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                _fetch_building_register_metrics_for_pnu,
                pnu,
                parcel_area_by_pnu.get(pnu),
            ): pnu
            for pnu in missing_pnu_list
        }
        for future in as_completed(future_map):
            pnu = future_map[future]
            try:
                metrics = future.result()
                metrics_by_pnu[pnu] = metrics
                fetched_rows.append(_metrics_to_cache_row(metrics, now=now))
            except Exception:
                metrics_by_pnu[pnu] = BuildingRegisterMetrics(pnu=pnu)
                errors.append(pnu)

    try:
        for row in fetched_rows:
            existing = db.query(BuildingRegisterCache).filter(BuildingRegisterCache.pnu == row.pnu).first()
            if existing is None:
                db.add(row)
                continue
            existing.has_building_register = row.has_building_register
            existing.building_count = row.building_count
            existing.aged_building_count = row.aged_building_count
            existing.residential_building_count = row.residential_building_count
            existing.approval_year_sum = row.approval_year_sum
            existing.approval_year_count = row.approval_year_count
            existing.average_approval_year = row.average_approval_year
            existing.total_floor_area_sqm = row.total_floor_area_sqm
            existing.site_area_sqm = row.site_area_sqm
            existing.floor_area_ratio = row.floor_area_ratio
            existing.primary_purpose_name = row.primary_purpose_name
            existing.synced_at = row.synced_at
            existing.updated_at = row.updated_at
            db.add(existing)
        db.flush()
    except (ProgrammingError, OperationalError):
        db.rollback()

    if errors:
        return BuildingRegisterBatchResult(
            metrics_by_pnu=metrics_by_pnu,
            ready=False,
            message=f"건축물대장 일부 조회에 실패했습니다. ({len(errors)}필지)",
        )
    return BuildingRegisterBatchResult(metrics_by_pnu=metrics_by_pnu, ready=True, message=None)


def _is_building_api_configured() -> bool:
    value = settings.bld_hub_service_key.strip()
    return bool(value and value != "your-building-hub-service-key")


def _cache_row_to_metrics(row: BuildingRegisterCache) -> BuildingRegisterMetrics:
    return BuildingRegisterMetrics(
        pnu=row.pnu,
        has_building_register=bool(row.has_building_register),
        building_count=int(row.building_count or 0),
        aged_building_count=int(row.aged_building_count or 0),
        residential_building_count=int(row.residential_building_count or 0),
        approval_year_sum=int(row.approval_year_sum or 0),
        approval_year_count=int(row.approval_year_count or 0),
        average_approval_year=row.average_approval_year,
        total_floor_area_sqm=row.total_floor_area_sqm,
        site_area_sqm=row.site_area_sqm,
        floor_area_ratio=row.floor_area_ratio,
        primary_purpose_name=row.primary_purpose_name,
    )


def _metrics_to_cache_row(metrics: BuildingRegisterMetrics, *, now: datetime) -> BuildingRegisterCache:
    return BuildingRegisterCache(
        pnu=metrics.pnu,
        has_building_register=metrics.has_building_register,
        building_count=metrics.building_count,
        aged_building_count=metrics.aged_building_count,
        residential_building_count=metrics.residential_building_count,
        approval_year_sum=metrics.approval_year_sum,
        approval_year_count=metrics.approval_year_count,
        average_approval_year=metrics.average_approval_year,
        total_floor_area_sqm=metrics.total_floor_area_sqm,
        site_area_sqm=metrics.site_area_sqm,
        floor_area_ratio=metrics.floor_area_ratio,
        primary_purpose_name=metrics.primary_purpose_name,
        synced_at=now,
        updated_at=now,
    )


def _fetch_building_register_metrics_for_pnu(pnu: str, parcel_area_sqm: float | None) -> BuildingRegisterMetrics:
    title_items = _fetch_building_items("getBrTitleInfo", pnu)
    items = title_items
    if not items:
        items = _fetch_building_items("getBrRecapTitleInfo", pnu)
    if not items:
        return BuildingRegisterMetrics(pnu=pnu)

    current_year = datetime.now(timezone.utc).year
    aged_threshold_year = current_year - max(1, settings.map_zone_aged_building_years)
    building_count = len(items)
    approval_years: list[int] = []
    purpose_names: list[str] = []
    total_floor_area_sqm = 0.0
    site_area_candidates: list[float] = []
    residential_building_count = 0
    aged_building_count = 0

    for item in items:
        approval_year = _extract_approval_year(item)
        if approval_year is not None:
            approval_years.append(approval_year)
            if approval_year <= aged_threshold_year:
                aged_building_count += 1

        purpose_name = _extract_purpose_name(item)
        if purpose_name:
            purpose_names.append(purpose_name)
            if _is_residential_purpose(purpose_name):
                residential_building_count += 1

        total_area = _extract_total_floor_area(item)
        if total_area is not None and total_area > 0:
            total_floor_area_sqm += total_area

        site_area = _extract_site_area(item)
        if site_area is not None and site_area > 0:
            site_area_candidates.append(site_area)

    site_area_sqm = max(site_area_candidates) if site_area_candidates else (float(parcel_area_sqm) if parcel_area_sqm else None)
    average_approval_year = round(sum(approval_years) / len(approval_years)) if approval_years else None
    floor_area_ratio = None
    if site_area_sqm and site_area_sqm > 0 and total_floor_area_sqm > 0:
        floor_area_ratio = round((total_floor_area_sqm / site_area_sqm) * 100, 2)

    purpose_counter = Counter(name for name in purpose_names if name and name.strip())
    primary_purpose_name = purpose_counter.most_common(1)[0][0] if purpose_counter else None

    return BuildingRegisterMetrics(
        pnu=pnu,
        has_building_register=True,
        building_count=building_count,
        aged_building_count=aged_building_count,
        residential_building_count=residential_building_count,
        approval_year_sum=sum(approval_years),
        approval_year_count=len(approval_years),
        average_approval_year=average_approval_year,
        total_floor_area_sqm=round(total_floor_area_sqm, 2) if total_floor_area_sqm > 0 else None,
        site_area_sqm=round(site_area_sqm, 2) if site_area_sqm is not None else None,
        floor_area_ratio=floor_area_ratio,
        primary_purpose_name=primary_purpose_name,
    )


def _fetch_building_items(endpoint: str, pnu: str) -> list[dict[str, Any]]:
    response = _call_building_hub_json(
        endpoint,
        {
            "sigunguCd": pnu[:5],
            "bjdongCd": pnu[5:10],
            "platGbCd": pnu[10],
            "bun": pnu[11:15],
            "ji": pnu[15:19],
            "numOfRows": "100",
            "pageNo": "1",
        },
    )
    body = response.get("body", {})
    items = body.get("items", {}).get("item", [])
    if isinstance(items, dict):
        return [items]
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]
    return []


def _call_building_hub_json(endpoint: str, params: dict[str, str]) -> dict[str, Any]:
    session = _get_building_session()
    response = session.get(
        f"{settings.bld_hub_api_base_url.rstrip('/')}/{endpoint.lstrip('/')}",
        params={
            "serviceKey": settings.bld_hub_service_key,
            "_type": "json",
            **params,
        },
        timeout=settings.bld_hub_timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    header = payload.get("response", {}).get("header", {})
    if str(header.get("resultCode", "")).strip() not in {"", "00"}:
        raise RuntimeError(str(header.get("resultMsg", "건축물대장 API 오류")).strip() or "건축물대장 API 오류")
    return payload.get("response", {})


def _get_building_session() -> requests.Session:
    global _BUILDING_SESSION
    if _BUILDING_SESSION is not None:
        return _BUILDING_SESSION

    retry = Retry(
        total=max(0, settings.bld_hub_retry_count),
        backoff_factor=max(0.0, settings.bld_hub_retry_backoff_seconds),
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    _BUILDING_SESSION = session
    return session


def _extract_approval_year(item: dict[str, Any]) -> int | None:
    text = str(item.get("useAprDay") or "").strip()
    if len(text) < 4 or not text[:4].isdigit():
        return None
    return int(text[:4])


def _extract_purpose_name(item: dict[str, Any]) -> str | None:
    for key in ("mainPurpsCdNm", "etcPurps"):
        value = str(item.get(key) or "").strip()
        if value:
            return value
    return None


def _extract_total_floor_area(item: dict[str, Any]) -> float | None:
    for key in ("totArea", "totDongTotArea", "vlRatEstmTotArea"):
        value = _to_positive_float(item.get(key))
        if value is not None:
            return value
    return None


def _extract_site_area(item: dict[str, Any]) -> float | None:
    return _to_positive_float(item.get("platArea"))


def _to_positive_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def _is_residential_purpose(value: str) -> bool:
    return any(keyword in value for keyword in _RESIDENTIAL_KEYWORDS)
