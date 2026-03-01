from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.bulk_job import BulkJob


def create_bulk_job(
    db: Session,
    *,
    job_id: str | None = None,
    user_id: str,
    file_name: str,
    upload_path: str,
    total_rows: int,
) -> BulkJob:
    payload = {
        "user_id": user_id,
        "file_name": file_name,
        "upload_path": upload_path,
        "total_rows": total_rows,
        "status": "queued",
    }
    if job_id:
        payload["id"] = job_id
    job = BulkJob(**payload)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_bulk_job_by_id(db: Session, job_id: str) -> BulkJob | None:
    stmt = select(BulkJob).where(BulkJob.id == job_id)
    return db.scalar(stmt)


def list_bulk_jobs_by_user(db: Session, user_id: str, limit: int = 50) -> list[BulkJob]:
    stmt = select(BulkJob).where(BulkJob.user_id == user_id).order_by(desc(BulkJob.created_at)).limit(limit)
    return list(db.scalars(stmt).all())


def update_bulk_job_status(
    db: Session,
    *,
    job: BulkJob,
    status: str,
    processed_rows: int | None = None,
    success_rows: int | None = None,
    failed_rows: int | None = None,
    result_path: str | None = None,
    error_message: str | None = None,
) -> BulkJob:
    job.status = status
    if processed_rows is not None:
        job.processed_rows = processed_rows
    if success_rows is not None:
        job.success_rows = success_rows
    if failed_rows is not None:
        job.failed_rows = failed_rows
    if result_path is not None:
        job.result_path = result_path
    if error_message is not None:
        job.error_message = error_message
    job.updated_at = datetime.now(timezone.utc)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job
