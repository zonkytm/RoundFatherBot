import enum
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TaskStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class ProcessingTask(Base):
    __tablename__ = "processing_tasks"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.PENDING)
    file_id: Mapped[str] = mapped_column(String(255))
    file_unique_id: Mapped[str] = mapped_column(String(255))
    input_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="tasks")
