import asyncio
import logging
import subprocess
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy import select

from bot.config import settings
from bot.handlers import handlers_router
from bot.middlewares.metrics import MetricsMiddleware
from bot.middlewares.rate_limit import RateLimitMiddleware
from bot.models.admin import Admin
from bot.models.base import async_session, engine
from bot.models.premium import PremiumPackage
from bot.models.preset import MailingPreset
from bot.models.user import User
from bot.services.notification_service import send_notifications
from web.routes.settings import seed_settings

SEED_PRESETS = [
    ("Каждый день в 10:00", "0 10 * * *", 1),
    ("Каждый день в 18:00", "0 18 * * *", 2),
    ("Каждый день в 9:00 и 18:00", "0 9,18 * * *", 3),
    ("Каждые 2 часа", "0 */2 * * *", 4),
    ("1-го числа каждого месяца", "0 10 1 * *", 5),
]

SEED_PACKAGES = [
    ("1 месяц", 30, 100, 199, 1),
    ("3 месяца", 90, 250, 499, 2),
    ("6 месяцев", 180, 450, 899, 3),
]


async def sync_admins():
    for admin_id in settings.ADMIN_IDS:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.telegram_id == admin_id))
            user = result.scalar_one_or_none()
            if not user:
                user = User(telegram_id=admin_id, first_name=f"Admin {admin_id}")
                session.add(user)
                await session.commit()
                await session.refresh(user)
            existing = await session.execute(
                select(Admin).where(Admin.user_id == user.id)
            )
            if not existing.scalar_one_or_none():
                session.add(Admin(user_id=user.id))
                await session.commit()


async def seed_presets():
    async with async_session() as session:
        result = await session.execute(select(MailingPreset).limit(1))
        if result.scalar_one_or_none():
            return
        for name, cron_expr, order in SEED_PRESETS:
            session.add(MailingPreset(name=name, cron_expr=cron_expr, sort_order=order))
        await session.commit()


async def seed_packages():
    async with async_session() as session:
        result = await session.execute(select(PremiumPackage).limit(1))
        if result.scalar_one_or_none():
            return
        for name, days, stars, rub, order in SEED_PACKAGES:
            session.add(
                PremiumPackage(
                    name=name,
                    duration_days=days,
                    price_stars=stars,
                    price_rub=rub,
                    sort_order=order,
                )
            )
        await session.commit()


async def on_startup(bot: Bot) -> None:
    Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(Path(__file__).resolve().parent.parent),
        check=True,
    )
    await seed_presets()
    await seed_packages()
    await seed_settings()
    await sync_admins()
    asyncio.create_task(send_notifications(bot))


async def on_shutdown() -> None:
    await engine.dispose()


def setup_logging() -> None:
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("%(levelname)-8s | %(name)s | %(message)s")
    )
    root_logger.addHandler(console_handler)


async def main() -> None:
    setup_logging()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.message.middleware(MetricsMiddleware())
    dp.message.middleware(RateLimitMiddleware(limit=settings.RATE_LIMIT_PER_MINUTE))
    dp.include_router(handlers_router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
