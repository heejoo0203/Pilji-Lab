from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import on_startup
from app.schemas.land import LandLookupRequest
from app.schemas.map import MapAddressSearchRequest, MapClickRequest
from app.services.map_service import (
    fetch_map_land_details,
    fetch_map_price_rows,
    lookup_map_by_address,
    lookup_map_by_click,
)
from app.services.vworld_service import lookup_land_prices


@dataclass
class CaseResult:
    case_id: str
    route: str
    status: str
    note: str


def _price_text_to_int(value: str) -> int:
    return int(value.replace(",", "").replace(" 원/㎡", "").strip())


def _format_int(value: int | None) -> str:
    if value is None:
        return "-"
    return f"{value:,}"


def _pass(case_id: str, route: str, note: str) -> CaseResult:
    return CaseResult(case_id=case_id, route=route, status="pass", note=note)


def _fail(case_id: str, route: str, note: str) -> CaseResult:
    return CaseResult(case_id=case_id, route=route, status="fail", note=note)


def _run_case_land_jibun(case_id: str, ld_code: str, main_no: str, sub_no: str) -> CaseResult:
    response = lookup_land_prices(
        LandLookupRequest(
            search_type="jibun",
            ld_code=ld_code,
            main_no=main_no,
            sub_no=sub_no,
            san_type="일반",
        )
    )
    if not response.rows:
        return _fail(case_id, "land/single:jibun", "rows=0")

    latest = response.rows[0]
    return _pass(
        case_id,
        "land/single:jibun",
        f"pnu={response.pnu}, latest={latest.기준년도}/{latest.개별공시지가}, 기준일자={latest.기준일자}",
    )


def _run_case_land_road(
    case_id: str,
    sido: str,
    sigungu: str,
    road_name: str,
    building_main_no: str,
) -> CaseResult:
    response = lookup_land_prices(
        LandLookupRequest(
            search_type="road",
            sido=sido,
            sigungu=sigungu,
            road_name=road_name,
            building_main_no=building_main_no,
            building_sub_no="",
        )
    )
    if not response.rows:
        return _fail(case_id, "land/single:road", "rows=0")

    latest = response.rows[0]
    return _pass(
        case_id,
        "land/single:road",
        f"pnu={response.pnu}, latest={latest.기준년도}/{latest.개별공시지가}, 기준일자={latest.기준일자}",
    )


def main() -> int:
    results: list[CaseResult] = []
    if os.environ.get("FORCE_DISABLE_REDIS") == "1" or os.environ.get("REDIS_URL", None) == "":
        settings.redis_url = ""
    on_startup()
    db = SessionLocal()

    try:
        try:
            results.append(_run_case_land_jibun("L-001", "1114010300", "31", "0"))
        except Exception as exc:  # pragma: no cover - operational smoke
            results.append(_fail("L-001", "land/single:jibun", str(exc)))

        try:
            results.append(_run_case_land_jibun("L-002", "1120011500", "269", "25"))
        except Exception as exc:  # pragma: no cover - operational smoke
            results.append(_fail("L-002", "land/single:jibun", str(exc)))

        try:
            results.append(_run_case_land_road("L-003", "서울특별시", "강남구", "압구정로", "165"))
        except Exception as exc:  # pragma: no cover - operational smoke
            results.append(_fail("L-003", "land/single:road", str(exc)))

        try:
            land = lookup_land_prices(
                LandLookupRequest(
                    search_type="road",
                    sido="서울특별시",
                    sigungu="마포구",
                    road_name="마포대로",
                    building_main_no="89",
                    building_sub_no="",
                )
            )
            mapped = lookup_map_by_address(db, MapAddressSearchRequest(address="서울특별시 마포구 마포대로 89"))
            matched = bool(land.rows) and mapped.price_current == _price_text_to_int(land.rows[0].개별공시지가)
            if matched:
                results.append(
                    _pass(
                        "L-004",
                        "land/single:road vs map/search",
                        f"pnu={mapped.pnu}, land={land.rows[0].개별공시지가}, map={_format_int(mapped.price_current)}",
                    )
                )
            else:
                results.append(
                    _fail(
                        "L-004",
                        "land/single:road vs map/search",
                        f"mismatch land={land.rows[0].개별공시지가 if land.rows else '-'}, map={_format_int(mapped.price_current)}",
                    )
                )
        except Exception as exc:  # pragma: no cover - operational smoke
            results.append(_fail("L-004", "land/single:road vs map/search", str(exc)))

        try:
            land = lookup_land_prices(
                LandLookupRequest(
                    search_type="road",
                    sido="경기도",
                    sigungu="성남시 분당구",
                    road_name="판교역로",
                    building_main_no="166",
                    building_sub_no="",
                )
            )
            mapped = lookup_map_by_address(db, MapAddressSearchRequest(address="경기도 성남시 분당구 판교역로 166"))
            price_rows = fetch_map_price_rows(mapped.pnu)
            land_details = fetch_map_land_details(mapped.pnu)
            matched = bool(land.rows) and bool(price_rows.rows) and mapped.price_current == _price_text_to_int(land.rows[0].개별공시지가)
            if matched:
                results.append(
                    _pass(
                        "L-005",
                        "land/single:road + map/search + map/price-rows + map/land-details",
                        (
                            f"pnu={mapped.pnu}, land={land.rows[0].개별공시지가}, "
                            f"map={_format_int(mapped.price_current)}, rows={len(price_rows.rows)}, area={land_details.area}"
                        ),
                    )
                )
            else:
                results.append(
                    _fail(
                        "L-005",
                        "land/single:road + map/search + map/price-rows + map/land-details",
                        f"mismatch land={land.rows[0].개별공시지가 if land.rows else '-'}, map={_format_int(mapped.price_current)}",
                    )
                )
        except Exception as exc:  # pragma: no cover - operational smoke
            results.append(_fail("L-005", "land/single:road + map/search", str(exc)))

        try:
            searched = lookup_map_by_address(db, MapAddressSearchRequest(address="경기도 성남시 분당구 판교역로 166"))
            clicked = lookup_map_by_click(db, MapClickRequest(lat=searched.lat, lng=searched.lng))
            matched = clicked.pnu == searched.pnu and clicked.price_current == searched.price_current
            if matched:
                results.append(
                    _pass(
                        "L-006",
                        "map/click",
                        f"pnu={clicked.pnu}, price={_format_int(clicked.price_current)}, address={clicked.address_summary}",
                    )
                )
            else:
                results.append(
                    _fail(
                        "L-006",
                        "map/click",
                        (
                            f"search={searched.pnu}/{_format_int(searched.price_current)}, "
                            f"click={clicked.pnu}/{_format_int(clicked.price_current)}"
                        ),
                    )
                )
        except Exception as exc:  # pragma: no cover - operational smoke
            results.append(_fail("L-006", "map/click", str(exc)))

        try:
            searched = lookup_map_by_address(db, MapAddressSearchRequest(address="경기도 성남시 분당구 판교역로 166"))
            clicked = lookup_map_by_click(db, MapClickRequest(lat=searched.lat, lng=searched.lng))
            matched = searched.pnu == clicked.pnu and searched.price_current == clicked.price_current
            if matched:
                results.append(
                    _pass(
                        "L-007",
                        "map/search",
                        f"pnu={searched.pnu}, price={_format_int(searched.price_current)}, address={searched.address_summary}",
                    )
                )
            else:
                results.append(
                    _fail(
                        "L-007",
                        "map/search",
                        (
                            f"search={searched.pnu}/{_format_int(searched.price_current)}, "
                            f"click={clicked.pnu}/{_format_int(clicked.price_current)}"
                        ),
                    )
                )
        except Exception as exc:  # pragma: no cover - operational smoke
            results.append(_fail("L-007", "map/search", str(exc)))
    finally:
        db.close()

    db_kind = settings.database_url.split(":", maxsplit=1)[0] or "unknown"
    passed = sum(1 for result in results if result.status == "pass")

    print(f"accuracy-golden-set basic lookup smoke: {passed}/{len(results)} passed")
    print(f"environment: db={db_kind}, redis={'on' if settings.redis_url else 'off'}, vworld=live")
    print("| 케이스 ID | 경로 | 결과 | 관측값 |")
    print("| --- | --- | --- | --- |")
    for result in results:
        print(f"| {result.case_id} | {result.route} | {result.status} | {result.note} |")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
