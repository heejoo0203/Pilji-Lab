from __future__ import annotations

from threading import Lock

from fastapi import HTTPException, status

from app.core.config import settings

CHOSEONG = ["ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]

_road_cache: dict[tuple[str, str], list[str]] = {}
_cache_lock = Lock()


def get_road_names(sido: str, sigungu: str, initial: str) -> list[str]:
    initial = normalize_text(initial)
    if not initial:
        return []

    roads = get_roads_by_area(sido, sigungu)
    return [name for name in roads if initial_consonant(name) == initial]


def get_roads_by_area(sido: str, sigungu: str) -> list[str]:
    key = (normalize_text(sido), normalize_text(sigungu))
    if not key[0] or not key[1]:
        return []

    with _cache_lock:
        cached = _road_cache.get(key)
    if cached is not None:
        return cached

    file_path = settings.road_name_file_path
    try:
        fp = open(file_path, "r", encoding="cp949", errors="ignore")
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "ROAD_FILE_NOT_FOUND", "message": f"도로명 파일을 찾을 수 없습니다: {file_path}"},
        ) from exc

    aliases = sigungu_aliases(key[1])
    roads: set[str] = set()
    with fp:
        for raw in fp:
            line = raw.rstrip("\r\n")
            if not line:
                continue
            cols = line.split("|")
            if len(cols) < 7:
                continue

            row_sido = normalize_text(cols[5])
            row_sigungu = normalize_text(cols[6])
            if row_sido != key[0]:
                continue
            if not sigungu_match(row_sigungu, aliases):
                continue

            road_name = normalize_text(cols[3])
            if road_name:
                roads.add(road_name)

    result = sorted(roads)
    with _cache_lock:
        _road_cache[key] = result
    return result


def sigungu_match(value: str, aliases: set[str]) -> bool:
    if value in aliases:
        return True
    compact = value.replace(" ", "")
    if compact in aliases:
        return True
    short = value.split(" ")[-1]
    return short in aliases


def sigungu_aliases(sigungu: str) -> set[str]:
    values = {sigungu, sigungu.replace(" ", "")}
    parts = sigungu.split(" ")
    if parts:
        values.add(parts[-1])
    return {v for v in values if v}


def normalize_text(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def initial_consonant(text: str) -> str:
    if not text:
        return ""
    first = text.strip()[:1]
    if not first:
        return ""
    code = ord(first)
    if "ㄱ" <= first <= "ㅎ":
        return first
    if code < 0xAC00 or code > 0xD7A3:
        return first.upper()
    index = (code - 0xAC00) // 588
    if 0 <= index < len(CHOSEONG):
        return CHOSEONG[index]
    return ""
