from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MailingPreset(Base):
    __tablename__ = "mailing_presets"

    name: Mapped[str] = mapped_column(String(255))
    cron_expr: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
