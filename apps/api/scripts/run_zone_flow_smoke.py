from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import uuid

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.map import (
    MapAddressSearchRequest,
    MapCoordinate,
    MapZoneAnalyzeRequest,
    MapZoneParcelDecisionRequest,
    MapZoneSaveRequest,
    MapZoneUpdateRequest,
)
from app.services.map_service import lookup_map_by_address
from app.services.map_zone_service import (
    analyze_zone,
    delete_zone_analysis,
    get_zone_detail,
    list_zone_analyses,
    save_zone_analysis,
    update_zone_name,
    update_zone_parcel_decisions,
)
from app.services.map_zone.geometry import is_postgres


@dataclass
class CaseResult:
    case_id: str
    route: str
    status: str
    note: str


def _square(lat: float, lng: float, delta: float = 0.00025) -> list[MapCoordinate]:
    return [
        MapCoordinate(lat=lat - delta, lng=lng - delta),
        MapCoordinate(lat=lat - delta, lng=lng + delta),
        MapCoordinate(lat=lat + delta, lng=lng + delta),
        MapCoordinate(lat=lat + delta, lng=lng - delta),
    ]


def _pass(case_id: str, route: str, note: str) -> CaseResult:
    return CaseResult(case_id=case_id, route=route, status="pass", note=note)


def _fail(case_id: str, route: str, note: str) -> CaseResult:
    return CaseResult(case_id=case_id, route=route, status="fail", note=note)


def main() -> int:
    if os.environ.get("FORCE_DISABLE_REDIS") == "1" or os.environ.get("REDIS_URL", None) == "":
        settings.redis_url = ""

    db = SessionLocal()
    results: list[CaseResult] = []
    user: User | None = None
    zone_ids: list[str] = []

    try:
        if not is_postgres(db):
            print("zone-flow smoke requires PostgreSQL/PostGIS")
            return 1

        user = User(
            email=f"codex-zone-smoke-{uuid.uuid4().hex[:8]}@example.com",
            password_hash="not-used",
            full_name="Codex Zone Smoke",
            role="user",
            auth_provider="local",
            terms_version="2026-03-05-v1",
            terms_snapshot="{}",
            terms_accepted_at=datetime.now(timezone.utc),
        )
        db.add(user)
        db.commit()

        lookup = lookup_map_by_address(db, MapAddressSearchRequest(address="서울특별시 마포구 마포대로 89"))
        coords = _square(lookup.lat, lookup.lng)

        try:
            preview = analyze_zone(
                db,
                payload=MapZoneAnalyzeRequest(zone_name="codex-zone-preview", coordinates=coords, overlap_threshold=0.9),
            )
            boundary_pnu_list = [item.pnu for item in preview.parcels if item.inclusion_mode == "boundary_candidate"]
            included_pnu_list = [item.pnu for item in preview.parcels if item.included]
            if preview.summary.parcel_count >= 1 and preview.summary.boundary_parcel_count >= 1:
                results.append(
                    _pass(
                        "Z-002",
                        "map/zones/analyze",
                        (
                            f"parcel_count={preview.summary.parcel_count}, "
                            f"boundary={preview.summary.boundary_parcel_count}, "
                            f"included={included_pnu_list[0] if included_pnu_list else '-'}"
                        ),
                    )
                )
            else:
                results.append(
                    _fail(
                        "Z-002",
                        "map/zones/analyze",
                        f"parcel_count={preview.summary.parcel_count}, boundary={preview.summary.boundary_parcel_count}",
                    )
                )
        except Exception as exc:  # pragma: no cover - operational smoke
            results.append(_fail("Z-002", "map/zones/analyze", str(exc)))
            boundary_pnu_list = []
            included_pnu_list = []

        try:
            saved_a = save_zone_analysis(
                db,
                user_id=user.id,
                payload=MapZoneSaveRequest(
                    zone_name="codex-zone-a",
                    coordinates=coords,
                    overlap_threshold=0.9,
                    included_pnu_list=[],
                    excluded_pnu_list=[],
                ),
            )
            if saved_a.summary.zone_id:
                zone_ids.append(saved_a.summary.zone_id)
            detail_a = get_zone_detail(db, user_id=user.id, zone_id=saved_a.summary.zone_id or "")
            listed = list_zone_analyses(db, user_id=user.id, page=1, page_size=10)
            if (
                saved_a.summary.parcel_count >= 1
                and listed.total_count >= 1
                and detail_a.summary.zone_id == saved_a.summary.zone_id
            ):
                results.append(
                    _pass(
                        "Z-008",
                        "map/zones save/list/get",
                        (
                            f"zone_id={saved_a.summary.zone_id}, parcel_count={saved_a.summary.parcel_count}, "
                            f"list_total={listed.total_count}"
                        ),
                    )
                )
            else:
                results.append(
                    _fail(
                        "Z-008",
                        "map/zones save/list/get",
                        (
                            f"saved={saved_a.summary.parcel_count}, "
                            f"detail={detail_a.summary.parcel_count}, list_total={listed.total_count}"
                        ),
                    )
                )
        except Exception as exc:  # pragma: no cover - operational smoke
            results.append(_fail("Z-008", "map/zones save/list/get", str(exc)))
            saved_a = None
            detail_a = None

        try:
            if saved_a is None or not boundary_pnu_list:
                raise RuntimeError("save preview boundary data unavailable")
            updated_include = update_zone_parcel_decisions(
                db,
                user_id=user.id,
                zone_id=saved_a.summary.zone_id or "",
                payload=MapZoneParcelDecisionRequest(
                    include_pnu_list=[boundary_pnu_list[0]],
                    exclude_pnu_list=[],
                    decision_origin="user",
                    reason="zone smoke include",
                ),
            )
            target = next(item for item in updated_include.parcels if item.pnu == boundary_pnu_list[0])
            if target.included and target.selection_origin == "user" and updated_include.summary.parcel_count >= 2:
                results.append(
                    _pass(
                        "Z-005",
                        "map/zones decision include",
                        f"pnu={target.pnu}, parcel_count={updated_include.summary.parcel_count}, mode={target.inclusion_mode}",
                    )
                )
            else:
                results.append(
                    _fail(
                        "Z-005",
                        "map/zones decision include",
                        (
                            f"pnu={target.pnu}, included={target.included}, "
                            f"origin={target.selection_origin}, parcel_count={updated_include.summary.parcel_count}"
                        ),
                    )
                )
        except Exception as exc:  # pragma: no cover - operational smoke
            results.append(_fail("Z-005", "map/zones decision include", str(exc)))

        try:
            if saved_a is None or not included_pnu_list:
                raise RuntimeError("save preview included data unavailable")
            updated_exclude = update_zone_parcel_decisions(
                db,
                user_id=user.id,
                zone_id=saved_a.summary.zone_id or "",
                payload=MapZoneParcelDecisionRequest(
                    include_pnu_list=[],
                    exclude_pnu_list=[included_pnu_list[0]],
                    decision_origin="user",
                    reason="zone smoke exclude",
                ),
            )
            target = next(item for item in updated_exclude.parcels if item.pnu == included_pnu_list[0])
            if (not target.included) and target.selection_origin == "user" and target.inclusion_mode == "user_excluded":
                results.append(
                    _pass(
                        "Z-006",
                        "map/zones decision exclude",
                        f"pnu={target.pnu}, parcel_count={updated_exclude.summary.parcel_count}, mode={target.inclusion_mode}",
                    )
                )
            else:
                results.append(
                    _fail(
                        "Z-006",
                        "map/zones decision exclude",
                        (
                            f"pnu={target.pnu}, included={target.included}, "
                            f"origin={target.selection_origin}, mode={target.inclusion_mode}"
                        ),
                    )
                )
            renamed = update_zone_name(
                db,
                user_id=user.id,
                zone_id=saved_a.summary.zone_id or "",
                payload=MapZoneUpdateRequest(zone_name="codex-zone-renamed"),
            )
            if renamed.summary.zone_name == "codex-zone-renamed":
                results.append(
                    _pass(
                        "Z-008R",
                        "map/zones rename",
                        f"zone_id={renamed.summary.zone_id}, zone_name={renamed.summary.zone_name}",
                    )
                )
            else:
                results.append(
                    _fail(
                        "Z-008R",
                        "map/zones rename",
                        f"zone_name={renamed.summary.zone_name}",
                    )
                )
        except Exception as exc:  # pragma: no cover - operational smoke
            results.append(_fail("Z-006", "map/zones decision exclude", str(exc)))

        try:
            saved_b = save_zone_analysis(
                db,
                user_id=user.id,
                payload=MapZoneSaveRequest(
                    zone_name="codex-zone-b",
                    coordinates=coords,
                    overlap_threshold=0.6,
                    included_pnu_list=[],
                    excluded_pnu_list=[],
                ),
            )
            if saved_b.summary.zone_id:
                zone_ids.append(saved_b.summary.zone_id)
            detail_a = get_zone_detail(db, user_id=user.id, zone_id=saved_a.summary.zone_id or "") if saved_a else None
            detail_b = get_zone_detail(db, user_id=user.id, zone_id=saved_b.summary.zone_id or "")
            current_included = {item.pnu for item in detail_b.parcels if item.included}
            baseline_included = {item.pnu for item in detail_a.parcels if item.included} if detail_a else set()
            added = sorted(current_included - baseline_included)
            if detail_b.summary.parcel_count > (detail_a.summary.parcel_count if detail_a else 0) and added:
                results.append(
                    _pass(
                        "Z-009",
                        "map/zones compare data-level",
                        (
                            f"baseline={detail_a.summary.parcel_count if detail_a else 0}, "
                            f"current={detail_b.summary.parcel_count}, added={','.join(added)}"
                        ),
                    )
                )
            else:
                results.append(
                    _fail(
                        "Z-009",
                        "map/zones compare data-level",
                        (
                            f"baseline={detail_a.summary.parcel_count if detail_a else 0}, "
                            f"current={detail_b.summary.parcel_count}, added={','.join(added)}"
                        ),
                    )
                )
        except Exception as exc:  # pragma: no cover - operational smoke
            results.append(_fail("Z-009", "map/zones compare data-level", str(exc)))
    finally:
        for zone_id in reversed(zone_ids):
            if user is None:
                break
            try:
                delete_zone_analysis(db, user_id=user.id, zone_id=zone_id)
            except Exception:
                db.rollback()
        if user is not None:
            try:
                db.delete(user)
                db.commit()
            except Exception:
                db.rollback()
        db.close()

    db_kind = settings.database_url.split(":", maxsplit=1)[0] or "unknown"
    passed = sum(1 for result in results if result.status == "pass")

    print(f"zone-flow smoke: {passed}/{len(results)} passed")
    print(f"environment: db={db_kind}, redis={'off' if not settings.redis_url else 'on'}, map=live, vworld=live")
    print("| 케이스 ID | 경로 | 결과 | 관측값 |")
    print("| --- | --- | --- | --- |")
    for result in results:
        print(f"| {result.case_id} | {result.route} | {result.status} | {result.note} |")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
