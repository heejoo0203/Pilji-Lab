from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import cast

from fastapi import HTTPException

from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.bulk_job_repository import get_bulk_job_by_id, update_bulk_job_status
from app.services.bulk.column_mapper import map_headers
from app.services.bulk.normalizer import AddressMode, normalize_lookup_row
from app.services.bulk.result_writer import write_result_workbook
from app.services.bulk.table_reader import load_tabular_data
from app.services.bulk.job_storage import get_result_file_path
from app.services.vworld_service import lookup_land_prices

PROGRESS_UPDATE_ROW_INTERVAL = 5


def process_bulk_job(*, job_id: str, address_mode: str) -> None:
    db = SessionLocal()
    job = None
    try:
        job = get_bulk_job_by_id(db, job_id)
        if not job:
            return

        update_bulk_job_status(db, job=job, status="processing", processed_rows=0, success_rows=0, failed_rows=0)

        table = load_tabular_data(Path(job.upload_path))
        if len(table.rows) > settings.bulk_max_rows:
            raise ValueError(f"업로드 가능한 최대 행 수({settings.bulk_max_rows:,}행)를 초과했습니다.")

        mapping = map_headers(table.headers)
        total_rows = len(table.rows)

        lookup_cache: dict[str, dict[str, Any]] = {}
        row_results: list[dict[str, Any]] = []
        year_set: set[str] = set()
        success_rows = 0
        failed_rows = 0
        processed_rows = 0

        for row in table.rows:
            processed_rows += 1
            try:
                normalized = normalize_lookup_row(
                    row=row,
                    mapping=mapping,
                    address_mode=cast(AddressMode, address_mode),
                )
                cached = lookup_cache.get(normalized.cache_key)
                if cached is None:
                    lookup = lookup_land_prices(normalized.payload)
                    year_values = _extract_year_values(lookup.rows)
                    cached = {
                        "pnu": lookup.pnu,
                        "address_summary": lookup.address_summary,
                        "year_values": year_values,
                    }
                    lookup_cache[normalized.cache_key] = cached

                year_values = cached["year_values"] if isinstance(cached.get("year_values"), dict) else {}
                year_set.update(year_values.keys())
                row_results.append(
                    {
                        "status": "완료",
                        "error_message": "",
                        "address_summary": cached.get("address_summary", normalized.summary),
                        "pnu": cached.get("pnu", ""),
                        "year_values": year_values,
                    }
                )
                success_rows += 1
            except Exception as exc:  # noqa: BLE001
                failed_rows += 1
                row_results.append(
                    {
                        "status": "오류",
                        "error_message": _extract_error_message(exc),
                        "address_summary": "",
                        "pnu": "",
                        "year_values": {},
                    }
                )

            if processed_rows % PROGRESS_UPDATE_ROW_INTERVAL == 0 or processed_rows == total_rows:
                update_bulk_job_status(
                    db,
                    job=job,
                    status="processing",
                    processed_rows=processed_rows,
                    success_rows=success_rows,
                    failed_rows=failed_rows,
                )

        year_columns = sorted(year_set, key=lambda value: int(value), reverse=True)
        output_path = get_result_file_path(job_id=job_id, original_name=job.file_name)
        write_result_workbook(
            output_path=output_path,
            headers=table.headers,
            original_rows=table.rows,
            year_columns=year_columns,
            row_results=row_results,
        )

        if job:
            update_bulk_job_status(
                db,
                job=job,
                status="completed",
                processed_rows=processed_rows,
                success_rows=success_rows,
                failed_rows=failed_rows,
                result_path=str(output_path),
                error_message=None,
            )
    except Exception as exc:  # noqa: BLE001
        if job:
            update_bulk_job_status(
                db,
                job=job,
                status="failed",
                error_message=_extract_error_message(exc),
            )
    finally:
        db.close()


def _extract_year_values(rows: list[Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in rows:
        year = str(getattr(row, "기준년도", "")).strip()
        price = str(getattr(row, "개별공시지가", "")).strip()
        if year and price:
            result[year] = price
    return result


def _extract_error_message(exc: Exception) -> str:
    if isinstance(exc, HTTPException):
        detail = exc.detail
        if isinstance(detail, str):
            return detail
        if isinstance(detail, dict):
            message = detail.get("message")
            if isinstance(message, str):
                return message
    return str(exc)[:500]
