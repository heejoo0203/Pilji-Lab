from __future__ import annotations

import re
from pathlib import Path

from app.core.config import settings


def ensure_storage_dirs() -> tuple[Path, Path]:
    root = Path(settings.bulk_storage_dir).expanduser().resolve()
    uploads_dir = root / "uploads"
    results_dir = root / "results"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    return uploads_dir, results_dir


def save_uploaded_file(*, job_id: str, original_name: str, content: bytes) -> Path:
    uploads_dir, _ = ensure_storage_dirs()
    safe_name = _sanitize_filename(original_name) or "uploaded.xlsx"
    ext = Path(safe_name).suffix.lower() or ".xlsx"
    upload_path = uploads_dir / f"{job_id}_{Path(safe_name).stem}{ext}"
    upload_path.write_bytes(content)
    return upload_path


def get_result_file_path(*, job_id: str, original_name: str) -> Path:
    _, results_dir = ensure_storage_dirs()
    safe_name = _sanitize_filename(original_name) or "result.xlsx"
    return results_dir / f"{job_id}_{Path(safe_name).stem}_result.xlsx"


def _sanitize_filename(file_name: str) -> str:
    name = Path(str(file_name or "")).name
    return re.sub(r"[^A-Za-z0-9가-힣._-]", "_", name)
