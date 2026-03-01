from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from app.core.config import settings

_ld_code_map: dict[tuple[str, str, str], str] | None = None
_ld_code_lock = Lock()


def resolve_ld_code(sido: str, sigungu: str, eupmyeondong: str) -> str | None:
    mapping = _get_ld_code_map()
    key = (_normalize_token(sido), _normalize_token(sigungu), _normalize_token(eupmyeondong))
    if not all(key):
        return None
    return mapping.get(key)


def _get_ld_code_map() -> dict[tuple[str, str, str], str]:
    global _ld_code_map
    if _ld_code_map is not None:
        return _ld_code_map

    with _ld_code_lock:
        if _ld_code_map is not None:
            return _ld_code_map
        _ld_code_map = _load_ld_code_map(Path(settings.ld_code_file_path))
    return _ld_code_map


def _load_ld_code_map(file_path: Path) -> dict[tuple[str, str, str], str]:
    if not file_path.exists():
        return {}

    with file_path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)

    result: dict[tuple[str, str, str], str] = {}
    if not isinstance(payload, dict):
        return result

    for sido, sigungu_map in payload.items():
        if not isinstance(sigungu_map, dict):
            continue
        for sigungu, dong_map in sigungu_map.items():
            if not isinstance(dong_map, dict):
                continue
            for dong, code in dong_map.items():
                code_text = str(code).strip()
                if len(code_text) != 10 or not code_text.isdigit():
                    continue
                key = (_normalize_token(str(sido)), _normalize_token(str(sigungu)), _normalize_token(str(dong)))
                result[key] = code_text
    return result


def _normalize_token(value: str) -> str:
    return "".join(str(value or "").strip().split())
