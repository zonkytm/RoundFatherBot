import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

from aiogram.types.input_file import FSInputFile
from arq.connections import RedisSettings

from bot.config import settings
from bot.models.base import async_session
from bot.models.task import ProcessingTask, TaskStatus
from bot.services.video_processor import cleanup_files, convert_to_video_note

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)


async def process_video_task(ctx: dict, task_id: int, video_path: str, chat_id: int) -> None:

    bot: Bot = ctx["bot"]
    start = time.monotonic()

    try:
        output_path = await convert_to_video_note(
            video_path,
            size=settings.VIDEO_NOTE_SIZE,
            duration=settings.VIDEO_MAX_DURATION,
        )

        await bot.send_video_note(chat_id=chat_id, video_note=FSInputFile(output_path))

        elapsed_ms = int((time.monotonic() - start) * 1000)
        output_size = Path(output_path).stat().st_size

        async with async_session() as session:
            task = await session.get(ProcessingTask, task_id)
            if task:
                task.status = TaskStatus.DONE
                task.processing_time_ms = elapsed_ms
                task.output_size = output_size
                await session.commit()

        await cleanup_files(video_path, output_path)

    except Exception as e:
        logger.exception("Task %d failed", task_id)
        async with async_session() as session:
            task = await session.get(ProcessingTask, task_id)
            if task:
                task.status = TaskStatus.ERROR
                task.error_message = str(e)[:500]
                await session.commit()
        await cleanup_files(video_path)


class WorkerSettings:
    functions = [process_video_task]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    max_jobs = 4
    poll_delay = 0.1
