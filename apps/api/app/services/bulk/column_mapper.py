from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.bulk.constants import HEADER_ALIASES


@dataclass(slots=True)
class ColumnMapping:
    index_by_field: dict[str, int]

    def get(self, row: list[str], field: str) -> str:
        idx = self.index_by_field.get(field)
        if idx is None or idx >= len(row):
            return ""
        return str(row[idx]).strip()


def map_headers(headers: list[str]) -> ColumnMapping:
    normalized_headers = [_normalize_header(h) for h in headers]
    index_by_field: dict[str, int] = {}

    for field, aliases in HEADER_ALIASES.items():
        candidates = {_normalize_header(alias) for alias in aliases}
        for idx, normalized in enumerate(normalized_headers):
            if normalized in candidates:
                index_by_field[field] = idx
                break
    return ColumnMapping(index_by_field=index_by_field)


def _normalize_header(value: str) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"[\s\-_()/\[\]{}]+", "", text)
