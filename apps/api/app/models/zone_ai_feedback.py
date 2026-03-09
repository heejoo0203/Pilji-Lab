import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ZoneAIFeedback(Base):
    __tablename__ = "zone_ai_feedbacks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("zone_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pnu: Mapped[str] = mapped_column(String(19), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ai_model_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ai_recommendation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    final_decision: Mapped[str] = mapped_column(String(20), nullable=False)
    decision_origin: Mapped[str] = mapped_column(String(20), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )
