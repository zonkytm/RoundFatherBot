import time
from collections import defaultdict

from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy import select

from bot.models.base import async_session
from bot.models.setting import BotSetting


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 5, window: int = 60):
        self.limit = limit
        self.window = window
        self._timestamps: dict[int, list[float]] = defaultdict(list)
        super().__init__()

    async def _get_limit(self) -> int:
        try:
            async with async_session() as session:
                result = await session.execute(
                    select(BotSetting).where(BotSetting.key == "rate_limit_per_minute")
                )
                setting = result.scalar_one_or_none()
                if setting:
                    return int(setting.value)
        except Exception:
            pass
        return self.limit

    async def __call__(self, handler, event: Message, data: dict):
        user_id = event.from_user.id
        now = time.monotonic()

        limit = await self._get_limit()

        self._timestamps[user_id] = [t for t in self._timestamps[user_id] if now - t < self.window]

        if len(self._timestamps[user_id]) >= limit:
            wait_time = int(self.window - (now - self._timestamps[user_id][0]))
            await event.answer(
                f"Too many videos. Wait {wait_time}s.",
            )
            return None

        self._timestamps[user_id].append(now)
        return await handler(event, data)
