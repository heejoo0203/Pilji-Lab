from __future__ import annotations

from pathlib import Path
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings  # noqa: E402


INITIAL_REVISION = "20260302_0001"


def _build_alembic_config() -> Config:
    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BASE_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    return config


def _needs_bootstrap_stamp(database_url: str) -> bool:
    engine = create_engine(database_url, future=True)
    try:
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = set(inspector.get_table_names())
            has_data_revision = False
            if "alembic_version" in tables:
                row = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).first()
                has_data_revision = bool(row and row[0])
    finally:
        engine.dispose()

    has_legacy_schema = "users" in tables or "bulk_jobs" in tables
    if not has_legacy_schema:
        return False
    return not has_data_revision


def main() -> int:
    cfg = _build_alembic_config()
    db_url = settings.database_url

    # 기존 DB(create_all 기반)에서 Alembic 도입 시 초기 리비전으로 stamp 처리한다.
    if _needs_bootstrap_stamp(db_url):
        command.stamp(cfg, INITIAL_REVISION)

    command.upgrade(cfg, "head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
