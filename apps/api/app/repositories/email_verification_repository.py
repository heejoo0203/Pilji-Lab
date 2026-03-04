from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.email_verification import EmailVerification


def create_email_verification(
    db: Session,
    *,
    purpose: str,
    email: str,
    full_name: str | None,
    code_hash: str,
    expires_at: datetime,
    max_attempts: int = 5,
    meta_json: str = "{}",
) -> EmailVerification:
    item = EmailVerification(
        purpose=purpose,
        email=email,
        full_name=full_name,
        code_hash=code_hash,
        expires_at=expires_at,
        max_attempts=max_attempts,
        meta_json=meta_json,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_email_verification_by_id(db: Session, verification_id: str) -> EmailVerification | None:
    stmt = select(EmailVerification).where(EmailVerification.id == verification_id)
    return db.scalar(stmt)


def invalidate_pending_verifications(
    db: Session,
    *,
    purpose: str,
    email: str,
    now: datetime,
) -> None:
    stmt = (
        update(EmailVerification)
        .where(
            EmailVerification.purpose == purpose,
            EmailVerification.email == email,
            EmailVerification.consumed_at.is_(None),
            EmailVerification.expires_at > now,
        )
        .values(consumed_at=now)
    )
    db.execute(stmt)
    db.commit()


def save_email_verification(db: Session, item: EmailVerification) -> EmailVerification:
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
