from datetime import datetime

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MailingLog(Base):
    __tablename__ = "mailing_logs"

    mailing_id: Mapped[int] = mapped_column(ForeignKey("mailings.id"), index=True)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_at: Mapped[datetime] = mapped_column()
