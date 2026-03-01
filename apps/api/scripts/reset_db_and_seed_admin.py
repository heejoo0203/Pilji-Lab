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
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        db.execute(delete(User))
        admin = User(
            email="admin@admin.com",
            full_name="admin",
            role="admin",
            auth_provider="local",
            password_hash=hash_password("admin1234"),
        )
        db.add(admin)
        db.commit()
        print("DB 초기화 및 admin 계정 생성 완료")
        print("닉네임: admin")
        print("이메일: admin@admin.com")
        print("비밀번호: admin1234")
    finally:
        db.close()


if __name__ == "__main__":
    main()
