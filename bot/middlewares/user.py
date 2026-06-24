import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User as TgUser
from sqlalchemy import select

from bot.models.base import async_session
from bot.models.user import User

logger = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = None

        if hasattr(event, "from_user") and event.from_user:
            tg_user = event.from_user
        elif isinstance(event, Update) and event.message and event.message.from_user:
            tg_user = event.message.from_user
        elif isinstance(event, Update) and event.callback_query and event.callback_query.from_user:
            tg_user = event.callback_query.from_user

        if not tg_user or tg_user.is_bot:
            return await handler(event, data)

        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == tg_user.id)
            )
            user = result.scalar_one_or_none()

            if not user:
                user = User(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.full_name,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                logger.info("Created new user: %s (id=%s)", tg_user.full_name, tg_user.id)

            data["db_user"] = user

        return await handler(event, data)
