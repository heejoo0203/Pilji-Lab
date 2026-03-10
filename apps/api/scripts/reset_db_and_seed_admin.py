import os
from pathlib import Path
import sys

from sqlalchemy import delete

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.security import hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app import models  # noqa: F401, E402
from app.models.user import User  # noqa: E402


def main() -> None:
    admin_email = os.getenv("ADMIN_SEED_EMAIL", "").strip()
    admin_password = os.getenv("ADMIN_SEED_PASSWORD", "").strip()
    admin_name = os.getenv("ADMIN_SEED_NAME", "admin").strip() or "admin"

    if not admin_email or not admin_password:
        raise SystemExit("ADMIN_SEED_EMAIL, ADMIN_SEED_PASSWORD 환경변수를 먼저 설정해 주세요.")

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        db.execute(delete(User))
        admin = User(
            email=admin_email,
            full_name=admin_name,
            role="admin",
            auth_provider="local",
            password_hash=hash_password(admin_password),
        )
        db.add(admin)
        db.commit()
        print("DB 초기화 및 admin 계정 생성 완료")
        print(f"닉네임: {admin_name}")
        print(f"이메일: {admin_email}")
        print("비밀번호: [환경변수에서 입력됨]")
    finally:
        db.close()


if __name__ == "__main__":
    main()
