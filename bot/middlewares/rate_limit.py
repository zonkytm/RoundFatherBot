import time
from collections import defaultdict

from aiogram import BaseMiddleware
from aiogram.types import Message


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limit: int = 5, window: int = 60):
        self.limit = limit
        self.window = window
        self._timestamps: dict[int, list[float]] = defaultdict(list)
        super().__init__()

    async def __call__(self, handler, event: Message, data: dict):
        user_id = event.from_user.id
        now = time.monotonic()

        self._timestamps[user_id] = [t for t in self._timestamps[user_id] if now - t < self.window]

        if len(self._timestamps[user_id]) >= self.limit:
            wait_time = int(self.window - (now - self._timestamps[user_id][0]))
            await event.answer(
                f"Too many videos. Wait {wait_time}s.",
            )
            return None

        self._timestamps[user_id].append(now)
        return await handler(event, data)
