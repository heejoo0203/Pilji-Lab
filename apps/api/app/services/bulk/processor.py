from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from pathlib import Path
import time
from typing import Any
from typing import cast

from fastapi import HTTPException

from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.bulk_job_repository import get_bulk_job_by_id, update_bulk_job_status
from app.services.bulk.column_mapper import map_headers
from app.services.bulk.normalizer import AddressMode, NormalizedLookupRow, normalize_lookup_row
from app.services.bulk.result_writer import write_result_workbook
from app.services.bulk.table_reader import load_tabular_data
from app.services.bulk.job_storage import get_result_file_path
from app.services.vworld_service import lookup_land_prices

PROGRESS_UPDATE_ROW_INTERVAL = 5
logger = logging.getLogger(__name__)


def process_bulk_job(*, job_id: str, address_mode: str) -> None:
    db = SessionLocal()
    job = None
    try:
        job = get_bulk_job_by_id(db, job_id)
        if not job:
            return

        update_bulk_job_status(db, job=job, status="processing", processed_rows=0, success_rows=0, failed_rows=0)

        t_start = time.monotonic()
        table = load_tabular_data(Path(job.upload_path))
        if len(table.rows) > settings.bulk_max_rows:
            raise ValueError(f"업로드 가능한 최대 행 수({settings.bulk_max_rows:,}행)를 초과했습니다.")

        mapping = map_headers(table.headers)
        total_rows = len(table.rows)

        row_results: list[dict[str, Any] | None] = [None] * total_rows
        cache_key_to_normalized: dict[str, NormalizedLookupRow] = {}
        cache_key_to_indexes: dict[str, list[int]] = {}
        year_set: set[str] = set()
        success_rows = 0
        failed_rows = 0
        processed_rows = 0
        last_progress_report_rows = 0
        last_progress_report_at = time.monotonic()

        # 1) 행 정규화 및 유니크 주소 키 추출
        t_normalize_start = time.monotonic()
        for index, row in enumerate(table.rows):
            try:
                normalized = normalize_lookup_row(
                    row=row,
                    mapping=mapping,
                    address_mode=cast(AddressMode, address_mode),
                )
                cache_key_to_normalized.setdefault(normalized.cache_key, normalized)
                cache_key_to_indexes.setdefault(normalized.cache_key, []).append(index)
            except Exception as exc:  # noqa: BLE001
                processed_rows += 1
                failed_rows += 1
                row_results[index] = (
                    {
                        "status": "오류",
                        "error_message": _extract_error_message(exc),
                        "address_summary": "",
                        "pnu": "",
                        "year_values": {},
                    }
                )
                last_progress_report_rows, last_progress_report_at = _report_progress_if_needed(
                    db=db,
                    job=job,
                    processed_rows=processed_rows,
                    success_rows=success_rows,
                    failed_rows=failed_rows,
                    total_rows=total_rows,
                    last_report_rows=last_progress_report_rows,
                    last_report_at=last_progress_report_at,
                )

        normalize_ms = int((time.monotonic() - t_normalize_start) * 1000)

        # 2) 유니크 주소 기준 병렬 조회
        t_lookup_start = time.monotonic()
        unique_count = len(cache_key_to_normalized)
        if unique_count > 0:
            max_workers = max(1, min(settings.bulk_lookup_workers, unique_count))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_key = {
                    executor.submit(_lookup_one_normalized, normalized): cache_key
                    for cache_key, normalized in cache_key_to_normalized.items()
                }

                for future in as_completed(future_to_key):
                    cache_key = future_to_key[future]
                    indexes = cache_key_to_indexes.get(cache_key, [])
                    if not indexes:
                        continue

                    normalized = cache_key_to_normalized[cache_key]
                    try:
                        cached = future.result()
                        year_values = cached["year_values"] if isinstance(cached.get("year_values"), dict) else {}
                        year_set.update(year_values.keys())
                        for index in indexes:
                            row_results[index] = {
                                "status": "완료",
                                "error_message": "",
                                "address_summary": cached.get("address_summary", normalized.summary),
                                "pnu": cached.get("pnu", ""),
                                "year_values": year_values,
                            }
                        success_rows += len(indexes)
                    except Exception as exc:  # noqa: BLE001
                        error_message = _extract_error_message(exc)
                        for index in indexes:
                            row_results[index] = {
                                "status": "오류",
                                "error_message": error_message,
                                "address_summary": "",
                                "pnu": "",
                                "year_values": {},
                            }
                        failed_rows += len(indexes)

                    processed_rows += len(indexes)
                    last_progress_report_rows, last_progress_report_at = _report_progress_if_needed(
                        db=db,
                        job=job,
                        processed_rows=processed_rows,
                        success_rows=success_rows,
                        failed_rows=failed_rows,
                        total_rows=total_rows,
                        last_report_rows=last_progress_report_rows,
                        last_report_at=last_progress_report_at,
                    )

        lookup_ms = int((time.monotonic() - t_lookup_start) * 1000)

        unresolved_count = sum(1 for item in row_results if item is None)
        if unresolved_count > 0:
            raise RuntimeError(f"내부 처리 오류: 결과가 없는 행이 {unresolved_count}건 있습니다.")

        finalized_results: list[dict[str, Any]] = [cast(dict[str, Any], item) for item in row_results]

        # 3) 결과 파일 생성
        t_write_start = time.monotonic()
        year_columns = sorted(year_set, key=lambda value: int(value), reverse=True)
        output_path = get_result_file_path(job_id=job_id, original_name=job.file_name)
        write_result_workbook(
            output_path=output_path,
            headers=table.headers,
            original_rows=table.rows,
            year_columns=year_columns,
            row_results=finalized_results,
        )
        write_ms = int((time.monotonic() - t_write_start) * 1000)

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

        total_ms = int((time.monotonic() - t_start) * 1000)
        logger.info(
            "bulk job completed job_id=%s total_rows=%s unique_keys=%s success=%s failed=%s "
            "timing_ms={normalize:%s,lookup:%s,write:%s,total:%s}",
            job_id,
            total_rows,
            unique_count,
            success_rows,
            failed_rows,
            normalize_ms,
            lookup_ms,
            write_ms,
            total_ms,
        )
    except Exception as exc:  # noqa: BLE001
        if job:
            update_bulk_job_status(
                db,
                job=job,
                status="failed",
                error_message=_extract_error_message(exc),
            )
        logger.exception("bulk job failed job_id=%s", job_id)
    finally:
        db.close()


def _lookup_one_normalized(normalized: NormalizedLookupRow) -> dict[str, Any]:
    lookup = lookup_land_prices(normalized.payload)
    year_values = _extract_year_values(lookup.rows)
    return {
        "pnu": lookup.pnu,
        "address_summary": lookup.address_summary,
        "year_values": year_values,
    }


def _report_progress_if_needed(
    *,
    db: Any,
    job: Any,
    processed_rows: int,
    success_rows: int,
    failed_rows: int,
    total_rows: int,
    last_report_rows: int,
    last_report_at: float,
) -> tuple[int, float]:
    if processed_rows <= last_report_rows and processed_rows < total_rows:
        return last_report_rows, last_report_at

    rows_delta = processed_rows - last_report_rows
    elapsed = time.monotonic() - last_report_at
    should_report = (
        processed_rows == total_rows
        or rows_delta >= PROGRESS_UPDATE_ROW_INTERVAL
        or elapsed >= settings.bulk_progress_update_min_seconds
    )
    if not should_report:
        return last_report_rows, last_report_at

    update_bulk_job_status(
        db,
        job=job,
        status="processing",
        processed_rows=processed_rows,
        success_rows=success_rows,
        failed_rows=failed_rows,
    )
    return processed_rows, time.monotonic()


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
