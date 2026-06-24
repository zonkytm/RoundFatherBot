import asyncio
import logging
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from croniter import croniter
from sqlalchemy import or_, select, update

from bot.models.admin import Admin
from bot.models.base import async_session
from bot.models.mailing import Mailing, MailingStatus, MailingTarget
from bot.models.mailing_log import MailingLog
from bot.models.user import User

logger = logging.getLogger(__name__)


def get_next_cron_time(cron_expr: str, after: datetime) -> datetime | None:
    try:
        cron = croniter(cron_expr, after)
        return cron.get_next(datetime)
    except (ValueError, KeyError):
        return None


async def send_notifications(bot: Bot):
    while True:
        try:
            async with async_session() as session:
                now = datetime.utcnow()
                result = await session.execute(
                    select(Mailing)
                    .where(
                        Mailing.status == MailingStatus.PENDING,
                        or_(Mailing.scheduled_at.is_(None), Mailing.scheduled_at <= now),
                    )
                    .limit(1)
                )
                mailing = result.scalar_one_or_none()

                if not mailing:
                    await asyncio.sleep(10)
                    continue

                await session.execute(
                    update(Mailing)
                    .where(Mailing.id == mailing.id)
                    .values(status=MailingStatus.SENDING)
                )
                await session.commit()

            async with async_session() as session:
                if mailing.target == MailingTarget.ALL:
                    result = await session.execute(select(User))
                    users = result.scalars().all()
                elif mailing.target == MailingTarget.ADMINS:
                    result = await session.execute(
                        select(User).join(Admin, User.id == Admin.user_id)
                    )
                    users = result.scalars().all()
                else:
                    users = []
                user_map = {u.telegram_id: u for u in users}

            sent = 0
            failed = 0
            blocked_ids = []
            for user_id in user_map:
                try:
                    await bot.send_message(user_id, mailing.text, parse_mode="HTML")
                    sent += 1
                except TelegramForbiddenError:
                    failed += 1
                    blocked_ids.append(user_id)
                except (TelegramBadRequest, Exception):
                    failed += 1
                await asyncio.sleep(0.05)

            if blocked_ids:
                async with async_session() as session:
                    await session.execute(
                        update(User)
                        .where(User.telegram_id.in_(blocked_ids))
                        .values(is_blocked=True)
                    )
                    await session.commit()

            async with async_session() as session:
                log = MailingLog(
                    mailing_id=mailing.id,
                    sent_count=sent,
                    failed_count=failed,
                    sent_at=datetime.utcnow(),
                )
                session.add(log)

                if mailing.cron_expression:
                    next_time = get_next_cron_time(mailing.cron_expression, datetime.utcnow())
                    if next_time and mailing.is_active:
                        await session.execute(
                            update(Mailing)
                            .where(Mailing.id == mailing.id)
                            .values(
                                status=MailingStatus.PENDING,
                                scheduled_at=next_time,
                                sent_count=sent,
                                failed_count=failed,
                                sent_at=datetime.utcnow(),
                            )
                        )
                    else:
                        await session.execute(
                            update(Mailing)
                            .where(Mailing.id == mailing.id)
                            .values(
                                status=MailingStatus.DONE,
                                sent_count=sent,
                                failed_count=failed,
                                sent_at=datetime.utcnow(),
                            )
                        )
                else:
                    await session.execute(
                        update(Mailing)
                        .where(Mailing.id == mailing.id)
                        .values(
                            status=MailingStatus.DONE,
                            sent_count=sent,
                            failed_count=failed,
                            sent_at=datetime.utcnow(),
                        )
                    )

                await session.commit()

            logger.info("Mailing '%s' done: sent=%d, failed=%d", mailing.name, sent, failed)

        except Exception as e:
            logger.exception("Notification sender error: %s", e)

        await asyncio.sleep(10)
