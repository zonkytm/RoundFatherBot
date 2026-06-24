from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from bot.config import settings


class IsAdmin(BaseFilter):
    async def __call__(self, event: TelegramObject) -> bool:
        user_id = getattr(event.from_user, "id", None) if hasattr(event, "from_user") else None
        if user_id is None:
            return False
        return user_id in settings.ADMIN_IDS
