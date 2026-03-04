import uuid
from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Parcel(Base):
    __tablename__ = "parcels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pnu: Mapped[str] = mapped_column(String(19), nullable=False, unique=True, index=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    area: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_current: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    price_previous: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
