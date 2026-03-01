from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.land import LandLookupRequest, LandLookupResponse, LandResultRow


def lookup_land_prices(payload: LandLookupRequest) -> LandLookupResponse:
    if not settings.vworld_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "VWORLD_KEY_MISSING", "message": "VWORLD_API_KEY 설정이 필요합니다."},
        )

    if payload.search_type == "jibun":
        pnu = compose_pnu(
            ld_code=payload.ld_code or "",
            is_san=payload.san_type == "산",
            main_no=payload.main_no or "",
            sub_no=payload.sub_no or "",
        )
        address_summary = f"{payload.ld_code} {payload.san_type} {payload.main_no}-{payload.sub_no or '0'}"
    else:
        resolved = resolve_pnu_from_road(payload)
        pnu = resolved["pnu"]
        address_summary = resolved["summary"]

    rows = fetch_individual_land_price_rows(pnu)
    return LandLookupResponse(
        search_type=payload.search_type,
        pnu=pnu,
        address_summary=address_summary,
        rows=rows,
    )


def compose_pnu(ld_code: str, is_san: bool, main_no: str, sub_no: str) -> str:
    if not re.fullmatch(r"\d{10}", ld_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_LD_CODE", "message": "ld_code는 10자리 숫자여야 합니다."},
        )

    main = parse_positive_int(main_no, "main_no")
    sub = parse_non_negative_int(sub_no or "0", "sub_no")
    if main > 9999 or sub > 9999:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_JIBUN_RANGE", "message": "본번/부번은 0~9999 범위여야 합니다."},
        )

    regstr = "2" if is_san else "1"
    return f"{ld_code}{regstr}{main:04d}{sub:04d}"


def resolve_pnu_from_road(payload: LandLookupRequest) -> dict[str, str]:
    road_number = str(payload.building_main_no or "")
    if payload.building_sub_no and str(payload.building_sub_no).strip():
        road_number = f"{road_number}-{str(payload.building_sub_no).strip()}"

    full_road_address = f"{payload.sido} {payload.sigungu} {payload.road_name} {road_number}".strip()

    coord_json = call_vworld_json(
        "/req/address",
        {
            "service": "address",
            "request": "getcoord",
            "version": "2.0",
            "crs": "epsg:4326",
            "address": full_road_address,
            "refine": "true",
            "simple": "false",
            "format": "json",
            "type": "road",
        },
    )

    response = coord_json.get("response", {})
    if response.get("status") != "OK":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ROAD_GEOCODE_FAILED", "message": "도로명 주소를 좌표로 변환하지 못했습니다."},
        )

    point = response.get("result", {}).get("point", {})
    x = point.get("x")
    y = point.get("y")
    if not x or not y:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ROAD_GEOCODE_EMPTY", "message": "도로명 주소 좌표 결과가 없습니다."},
        )

    parcel_json = call_vworld_json(
        "/req/address",
        {
            "service": "address",
            "request": "getaddress",
            "version": "2.0",
            "crs": "epsg:4326",
            "point": f"{x},{y}",
            "format": "json",
            "type": "parcel",
            "simple": "false",
        },
    )
    parcel_resp = parcel_json.get("response", {})
    if parcel_resp.get("status") != "OK":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PARCEL_REVERSE_GEOCODE_FAILED", "message": "지번 주소 변환에 실패했습니다."},
        )

    result = parcel_resp.get("result") or []
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PARCEL_NOT_FOUND", "message": "지번 정보를 찾지 못했습니다."},
        )

    first = result[0]
    structure = first.get("structure", {})
    ld_code = str(structure.get("level4LC", "")).strip()
    level5 = str(structure.get("level5", "")).strip()
    if not ld_code or not level5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "PARCEL_DATA_INVALID", "message": "지번 변환 데이터가 올바르지 않습니다."},
        )

    parsed = parse_level5_jibun(level5)
    pnu = compose_pnu(
        ld_code=ld_code,
        is_san=parsed["is_san"],
        main_no=str(parsed["main_no"]),
        sub_no=str(parsed["sub_no"]),
    )
    return {"pnu": pnu, "summary": str(first.get("text", full_road_address))}


def parse_level5_jibun(level5: str) -> dict[str, Any]:
    text = level5.strip()
    is_san = text.startswith("산")
    text = text.replace("산", "", 1).strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_LEVEL5_JIBUN", "message": "지번 값이 비어 있습니다."},
        )
    if "-" in text:
        main_text, sub_text = text.split("-", 1)
    else:
        main_text, sub_text = text, "0"
    main = parse_positive_int(main_text, "level5.main")
    sub = parse_non_negative_int(sub_text, "level5.sub")
    return {"is_san": is_san, "main_no": main, "sub_no": sub}


def fetch_individual_land_price_rows(pnu: str) -> list[LandResultRow]:
    data = call_vworld_json(
        "/ned/data/getIndvdLandPriceAttr",
        {
            "pnu": pnu,
            "format": "json",
            "numOfRows": "1000",
            "pageNo": "1",
        },
    )
    root = data.get("indvdLandPrices") or {}
    result_code = str(root.get("resultCode", "") or "")
    result_msg = str(root.get("resultMsg", "") or "")
    if result_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": f"VWORLD_{result_code}", "message": result_msg or "VWorld 응답 오류"},
        )

    fields = root.get("field") or []
    if isinstance(fields, dict):
        fields = [fields]
    if not isinstance(fields, list):
        fields = []

    # 같은 연도 데이터가 여러 건인 경우, 최신 lastUpdtDt를 우선 선택.
    by_year: dict[str, dict[str, Any]] = {}
    for item in fields:
        if not isinstance(item, dict):
            continue
        year = str(item.get("stdrYear", "")).strip()
        if not year:
            continue
        prev = by_year.get(year)
        if prev is None:
            by_year[year] = item
            continue
        prev_date = str(prev.get("lastUpdtDt", "")).strip()
        cur_date = str(item.get("lastUpdtDt", "")).strip()
        if cur_date > prev_date:
            by_year[year] = item

    sorted_years = sorted(by_year.keys(), key=lambda x: int(x), reverse=True)
    rows: list[LandResultRow] = []
    for year in sorted_years:
        item = by_year[year]
        stdr_mt = str(item.get("stdrMt", "")).zfill(2)
        pblntf_pclnd = to_price_text(item.get("pblntfPclnd"))
        notice_date = str(item.get("pblntfDe", "")).replace("-", "")
        land_nm = str(item.get("ldCodeNm", "")).strip()
        mnnm_slno = str(item.get("mnnmSlno", "")).strip()
        regstr_nm = str(item.get("regstrSeCodeNm", "")).strip()
        jibun = format_jibun(mnnm_slno, regstr_nm)
        note = "표준지" if str(item.get("stdLandAt", "")).upper() == "Y" else ""

        rows.append(
            LandResultRow(
                기준년도=year,
                토지소재지=land_nm,
                지번=jibun,
                개별공시지가=pblntf_pclnd,
                기준일자=f"{stdr_mt}월 01일" if stdr_mt.strip("0") else "",
                공시일자=notice_date,
                비고=note,
            )
        )
    return rows


def format_jibun(mnnm_slno: str, regstr_nm: str) -> str:
    text = mnnm_slno.strip()
    if text.endswith("-0"):
        text = text[:-2]
    if regstr_nm == "산":
        return f"산 {text}"
    return text


def to_price_text(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        return f"{int(raw):,} 원/㎡"
    except ValueError:
        return f"{raw} 원/㎡"


def parse_positive_int(value: str, field_name: str) -> int:
    return _parse_int(value, field_name, allow_zero=False)


def parse_non_negative_int(value: str, field_name: str) -> int:
    return _parse_int(value, field_name, allow_zero=True)


def _parse_int(value: str, field_name: str, allow_zero: bool) -> int:
    text = str(value).strip()
    if not re.fullmatch(r"\d+", text):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_NUMBER", "message": f"{field_name}는 숫자여야 합니다."},
        )
    parsed = int(text)
    if allow_zero:
        if parsed < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_NUMBER", "message": f"{field_name}는 0 이상이어야 합니다."},
            )
    else:
        if parsed <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_NUMBER", "message": f"{field_name}는 1 이상이어야 합니다."},
            )
    return parsed


def call_vworld_json(path: str, params: dict[str, str]) -> dict[str, Any]:
    merged = dict(params)
    merged["key"] = settings.vworld_api_key
    merged["domain"] = settings.vworld_api_domain

    query = urlencode(merged, doseq=True)
    url = f"{settings.vworld_api_base_url.rstrip('/')}{path}?{query}"
    req = Request(url=url, method="GET", headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=settings.vworld_timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "VWORLD_HTTP_ERROR", "message": f"VWorld HTTP 오류: {exc.code}"},
        ) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "VWORLD_UNREACHABLE", "message": f"VWorld 연결 실패: {exc.reason}"},
        ) from exc

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "VWORLD_INVALID_JSON", "message": "VWorld 응답을 해석하지 못했습니다."},
        ) from exc
