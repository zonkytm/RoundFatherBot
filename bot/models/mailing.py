import enum
from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MailingStatus(enum.StrEnum):
    PENDING = "pending"
    SENDING = "sending"
    DONE = "done"
    FAILED = "failed"


class MailingTarget(enum.StrEnum):
    ALL = "all"
    ADMINS = "admins"


class Mailing(Base):
    __tablename__ = "mailings"

    name: Mapped[str] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text)
    target: Mapped[MailingTarget] = mapped_column(default=MailingTarget.ALL)
    status: Mapped[MailingStatus] = mapped_column(default=MailingStatus.PENDING)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
