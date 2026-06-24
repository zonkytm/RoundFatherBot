from datetime import datetime, timedelta

from sqlalchemy import func, select

from bot.models.base import async_session
from bot.models.task import ProcessingTask, TaskStatus
from bot.models.user import User


async def get_stats() -> dict:
    async with async_session() as session:
        now = datetime.utcnow()
        day_ago = now - timedelta(hours=24)

        total_users = (await session.execute(select(func.count(User.id)))).scalar() or 0
        active_users = (
            await session.execute(select(func.count(User.id)).where(User.is_blocked == False))
        ).scalar() or 0
        blocked_users = total_users - active_users
        users_24h = (
            await session.execute(select(func.count(User.id)).where(User.created_at >= day_ago))
        ).scalar() or 0

        total_videos = (
            await session.execute(
                select(func.count(ProcessingTask.id)).where(
                    ProcessingTask.status == TaskStatus.DONE
                )
            )
        ).scalar() or 0
        videos_24h = (
            await session.execute(
                select(func.count(ProcessingTask.id)).where(
                    ProcessingTask.status == TaskStatus.DONE,
                    ProcessingTask.created_at >= day_ago,
                )
            )
        ).scalar() or 0

        avg_time = (
            await session.execute(
                select(func.avg(ProcessingTask.processing_time_ms)).where(
                    ProcessingTask.status == TaskStatus.DONE,
                    ProcessingTask.processing_time_ms.isnot(None),
                )
            )
        ).scalar() or 0

        errors = (
            await session.execute(
                select(func.count(ProcessingTask.id)).where(
                    ProcessingTask.status == TaskStatus.ERROR
                )
            )
        ).scalar() or 0

        return {
            "total_users": total_users,
            "active_users": active_users,
            "blocked_users": blocked_users,
            "users_24h": users_24h,
            "total_videos": total_videos,
            "videos_24h": videos_24h,
            "avg_time_ms": int(avg_time),
            "errors": errors,
        }


async def get_hourly_activity() -> list[dict]:
    async with async_session() as session:
        now = datetime.utcnow()
        day_ago = now - timedelta(hours=24)

        result = await session.execute(
            select(
                func.date_trunc("hour", ProcessingTask.created_at).label("hour"),
                func.count(ProcessingTask.id).label("count"),
            )
            .where(ProcessingTask.created_at >= day_ago)
            .group_by("hour")
            .order_by("hour")
        )

        return [{"hour": row.hour, "count": row.count} for row in result]
