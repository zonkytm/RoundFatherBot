import logging
from datetime import datetime

from aiogram import Bot

from bot.config import settings
from bot.models.base import async_session
from bot.models.mailing import Mailing, MailingTarget
from bot.models.user import User

logger = logging.getLogger(__name__)


async def broadcast(bot: Bot, mailing: Mailing) -> int:
    async with async_session() as session:
        if mailing.target == MailingTarget.ALL:
            result = await session.execute(User.__table__.select())
        elif mailing.target == MailingTarget.ADMINS:
            from bot.models.admin import Admin

            result = await session.execute(
                User.__table__.select().join(Admin, User.id == Admin.user_id)
            )
        else:
            return 0

        users = result.scalars().all()

    sent = 0
    for user in users:
        try:
            await bot.send_message(chat_id=user.telegram_id, text=mailing.text)
            sent += 1
        except Exception as e:
            logger.warning("Failed to send to %d: %s", user.telegram_id, e)

    async with async_session() as session:
        m = await session.get(Mailing, mailing.id)
        if m:
            m.last_sent_at = datetime.utcnow()
            await session.commit()

    return sent


async def send_error_notification(bot: Bot, error: str) -> None:
    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=f"<b>Bot Error</b>\n\n{error}",
            )
        except Exception:
            logger.exception("Failed to notify admin %d", admin_id)
