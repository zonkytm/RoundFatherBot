import logging
import time
from datetime import datetime, timedelta
from pathlib import Path

from aiogram import F, Router
from aiogram.types import Message
from aiogram.types.input_file import FSInputFile
from sqlalchemy import func, select

from bot.config import settings
from bot.metrics import VIDEO_PROCESSING_COUNT, VIDEO_PROCESSING_LATENCY
from bot.models.base import async_session
from bot.models.setting import BotSetting
from bot.models.task import ProcessingTask, TaskStatus
from bot.models.user import User
from bot.services.video_processor import cleanup_files, convert_to_video_note

logger = logging.getLogger(__name__)
video_router = Router()


@video_router.message(F.video | F.video_note)
async def handle_video(message: Message, db_user: User) -> None:
    status_msg = await message.answer("Downloading video...")
    start = time.monotonic()

    async with async_session() as session:
        user = await session.get(User, db_user.id)

        if user.is_blocked:
            user.is_blocked = False
            await session.commit()

        if not user.is_premium:
            limit_setting = (
                await session.execute(select(BotSetting).where(BotSetting.key == "daily_limit"))
            ).scalar_one_or_none()
            daily_limit = int(limit_setting.value) if limit_setting else 10

            day_ago = datetime.utcnow() - timedelta(hours=24)
            today_count = (
                await session.execute(
                    select(func.count(ProcessingTask.id)).where(
                        ProcessingTask.user_id == user.id,
                        ProcessingTask.status == TaskStatus.DONE,
                        ProcessingTask.created_at >= day_ago,
                    )
                )
            ).scalar() or 0

            if today_count >= daily_limit:
                await status_msg.edit_text(
                    "\u26a0\ufe0f <b>Daily limit reached!</b>\n\n"
                    f"You processed <b>{today_count}</b> videos today.\n"
                    f"Limit: <b>{daily_limit}/day</b>\n\n"
                    "Get <b>premium</b> for unlimited processing: /premium"
                )
                return

        task = ProcessingTask(
            user_id=user.id,
            file_id=getattr(message.video or message.video_note, "file_id", ""),
            file_unique_id=getattr(message.video or message.video_note, "file_unique_id", ""),
            input_size=getattr(message.video or message.video_note, "file_size", 0),
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)

    input_path = None
    output_path = None

    try:
        if message.video:
            file = await message.bot.get_file(message.video.file_id)
            file_size_mb = (message.video.file_size or 0) / (1024 * 1024)
        elif message.video_note:
            file = await message.bot.get_file(message.video_note.file_id)
            file_size_mb = (message.video_note.file_size or 0) / (1024 * 1024)
        else:
            return

        if file_size_mb > settings.VIDEO_MAX_SIZE_MB:
            await status_msg.edit_text(
                f"File too large ({file_size_mb:.1f}MB). Max: {settings.VIDEO_MAX_SIZE_MB}MB."
            )
            return

        input_path = str(Path(settings.TEMP_DIR) / f"{file.file_unique_id}.mp4")
        Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
        await message.bot.download_file(file.file_path, input_path)

        await status_msg.edit_text("Converting to circle video...")

        output_path = await convert_to_video_note(
            input_path,
            size=settings.VIDEO_NOTE_SIZE,
            duration=settings.VIDEO_MAX_DURATION,
        )

        await message.answer_video_note(video_note=FSInputFile(output_path))

        elapsed_ms = int((time.monotonic() - start) * 1000)
        async with async_session() as session:
            t = await session.get(ProcessingTask, task.id)
            t.status = TaskStatus.DONE
            t.processing_time_ms = elapsed_ms
            t.output_size = Path(output_path).stat().st_size
            t.completed_at = datetime.utcnow()
            await session.commit()

        await status_msg.delete()

        VIDEO_PROCESSING_COUNT.labels(status="success").inc()
        VIDEO_PROCESSING_LATENCY.observe(time.monotonic() - start)

    except Exception as e:
        logger.exception("Video processing failed")
        async with async_session() as session:
            t = await session.get(ProcessingTask, task.id)
            t.status = TaskStatus.ERROR
            t.error_message = str(e)[:500]
            await session.commit()
        await status_msg.edit_text("Error processing video")

        VIDEO_PROCESSING_COUNT.labels(status="error").inc()

    finally:
        if input_path:
            await cleanup_files(input_path)
        if output_path:
            await cleanup_files(output_path)
