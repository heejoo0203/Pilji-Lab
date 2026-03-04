from __future__ import annotations

import smtplib
from email.message import EmailMessage

from fastapi import HTTPException, status

from app.core.config import settings


def send_email(*, to_email: str, subject: str, body: str) -> None:
    if settings.mail_delivery_mode == "console":
        print(f"[MAIL][TO={to_email}] {subject}\n{body}")
        return

    if not settings.smtp_host or not settings.mail_from:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "MAIL_CONFIG_INVALID", "message": "이메일 발송 설정이 올바르지 않습니다."},
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.mail_from
    message["To"] = to_email
    message.set_content(body)

    try:
        if settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
                _smtp_login_if_needed(smtp)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                _smtp_login_if_needed(smtp)
                smtp.send_message(message)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "MAIL_SEND_FAILED", "message": f"이메일 발송에 실패했습니다: {exc}"},
        ) from exc


def _smtp_login_if_needed(smtp: smtplib.SMTP) -> None:
    if settings.smtp_user:
        smtp.login(settings.smtp_user, settings.smtp_password)
