from __future__ import annotations

import os
from pathlib import Path
import sys

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session


BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.repositories.user_repository import get_user_by_email  # noqa: E402


INITIAL_REVISION = "20260302_0001"


def _admin_seed_config() -> tuple[str, str, str]:
    email = settings.admin_seed_email.strip() or os.getenv("ADMIN_SEED_EMAIL", "").strip()
    password = settings.admin_seed_password.strip() or os.getenv("ADMIN_SEED_PASSWORD", "").strip()
    name = settings.admin_seed_name.strip() or os.getenv("ADMIN_SEED_NAME", "admin").strip() or "admin"
    return email, password, name


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

    has_legacy_schema = "users" in tables or "bulk_jobs" in tables or "query_logs" in tables
    if not has_legacy_schema:
        return False
    return not has_data_revision


def _detect_bootstrap_revision(database_url: str) -> str:
    engine = create_engine(database_url, future=True)
    try:
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = set(inspector.get_table_names())
    finally:
        engine.dispose()

    if "query_logs" in tables:
        return "20260302_0002"
    return INITIAL_REVISION


def _seed_default_admin() -> None:
    db: Session = SessionLocal()
    try:
        admin_email, admin_password, admin_name = _admin_seed_config()
        existing = get_user_by_email(db, admin_email) if admin_email else None
        if existing and existing.role == "admin":
            print(f"[migrations] existing admin confirmed: {admin_email}")
            return
        if existing and existing.role != "admin":
            raise SystemExit(
                "[migrations] ADMIN_SEED_EMAIL 이 일반 사용자 계정과 충돌합니다. 다른 이메일을 사용하거나 해당 계정을 관리자 승격해 주세요."
            )

        existing_admin = db.query(User).filter(User.role == "admin").order_by(User.created_at.asc()).first()
        if existing_admin:
            print(f"[migrations] existing admin already present: {existing_admin.email}")
            return

        if not admin_email or not admin_password:
            raise SystemExit(
                "[migrations] 관리자 계정이 없고 ADMIN_SEED_EMAIL / ADMIN_SEED_PASSWORD 도 설정되지 않았습니다. "
                "첫 운영 배포 전에 관리자 시드 변수를 반드시 설정해 주세요."
            )

        admin = User(
            email=admin_email,
            password_hash=hash_password(admin_password),
            full_name=admin_name,
            role="admin",
            auth_provider="local",
        )
        db.add(admin)
        db.commit()
        print(f"[migrations] default admin created: {admin_email}")
    finally:
        db.close()


def main() -> int:
    cfg = _build_alembic_config()
    db_url = settings.database_url

    # 기존 DB(create_all 기반)에서 Alembic 도입 시 초기 리비전으로 stamp 처리한다.
    if _needs_bootstrap_stamp(db_url):
        command.stamp(cfg, _detect_bootstrap_revision(db_url))

    command.upgrade(cfg, "head")
    _seed_default_admin()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
