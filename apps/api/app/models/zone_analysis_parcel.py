import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ZoneAnalysisParcel(Base):
    __tablename__ = "zone_analysis_parcels"
    __table_args__ = (UniqueConstraint("zone_analysis_id", "pnu", name="uq_zone_analysis_parcel"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    zone_analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("zone_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pnu: Mapped[str] = mapped_column(String(19), nullable=False, index=True)
    jibun_address: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    road_address: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    land_category_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    purpose_area_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    area_sqm: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    overlap_area_sqm: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    price_current: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    price_year: Mapped[str | None] = mapped_column(String(4), nullable=True)
    overlap_ratio: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    centroid_in: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    selected_by_rule: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    inclusion_mode: Mapped[str] = mapped_column(String(30), nullable=False, default="excluded")
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    ai_recommendation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_reason_codes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_reason_text: Mapped[str | None] = mapped_column(String(300), nullable=True)
    ai_model_version: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ai_applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    selection_origin: Mapped[str] = mapped_column(String(20), nullable=False, default="rule")
    anomaly_codes: Mapped[str | None] = mapped_column(Text, nullable=True)
    anomaly_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    building_confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    household_confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    floor_area_ratio_confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)
    included: Mapped[bool] = mapped_column(nullable=False, default=True)
    excluded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    excluded_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
