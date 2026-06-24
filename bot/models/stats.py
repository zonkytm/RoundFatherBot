from datetime import datetime

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StatsHourly(Base):
    __tablename__ = "stats_hourly"

    hour: Mapped[datetime] = mapped_column(unique=True, index=True)
    videos_processed: Mapped[int] = mapped_column(Integer, default=0)
    videos_failed: Mapped[int] = mapped_column(Integer, default=0)
    unique_users: Mapped[int] = mapped_column(Integer, default=0)
    avg_processing_time_ms: Mapped[int] = mapped_column(Integer, default=0)
