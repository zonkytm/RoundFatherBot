from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import func, select

from bot.models.base import async_session
from bot.models.premium import PremiumPackage
from bot.models.setting import BotSetting
from bot.models.task import ProcessingTask, TaskStatus
from bot.models.user import User

status_router = Router()


async def _get_status_text(user_id: int) -> tuple[str, bool]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return "You haven't used the bot yet.\nSend me a video to get started!", False

        if user.is_premium:
            expires = user.premium_expires_at
            if expires and expires > datetime.utcnow():
                days_left = (expires - datetime.utcnow()).days
                text = (
                    f"\u2b50 <b>Premium Active</b>\n"
                    f"Expires: {expires.strftime('%d.%m.%Y')} ({days_left} days left)\n"
                    f"Limit: \u221e (unlimited)"
                )
            else:
                text = (
                    "\u274c <b>Premium Expired</b>\n"
                    "Your premium subscription has expired."
                )
            return text, True
        else:
            limit_setting = (
                await session.execute(
                    select(BotSetting).where(BotSetting.key == "daily_limit")
                )
            ).scalar_one_or_none()
            daily_limit = int(limit_setting.value) if limit_setting else user.daily_limit

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

            remaining = max(0, daily_limit - today_count)
            text = (
                f"\U0001f4ca <b>Your Stats</b>\n\n"
                f"Videos today: <b>{today_count}/{daily_limit}</b>\n"
                f"Remaining: <b>{remaining}</b>"
            )
            return text, False


@status_router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    text, is_premium = await _get_status_text(message.from_user.id)

    builder = InlineKeyboardBuilder()
    if not is_premium:
        builder.row(
            InlineKeyboardButton(
                text="\u2b50 Buy Premium",
                callback_data="show_premium",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="\U0001f4e1 Help",
            callback_data="help",
        )
    )

    await message.answer(text, reply_markup=builder.as_markup())


@status_router.callback_query(F.data == "my_status")
async def callback_my_status(callback: CallbackQuery) -> None:
    text, is_premium = await _get_status_text(callback.from_user.id)

    builder = InlineKeyboardBuilder()
    if not is_premium:
        builder.row(
            InlineKeyboardButton(
                text="\u2b50 Buy Premium",
                callback_data="show_premium",
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="\U0001f4e1 Help",
            callback_data="help",
        )
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@status_router.callback_query(F.data == "show_premium")
async def callback_show_premium(callback: CallbackQuery) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(PremiumPackage)
            .where(PremiumPackage.is_active)
            .order_by(PremiumPackage.sort_order)
        )
        packages = result.scalars().all()

    if not packages:
        await callback.answer("Premium not available yet.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for pkg in packages:
        builder.row(
            InlineKeyboardButton(
                text=f"\u2b50 {pkg.name} \u2014 {pkg.price_stars}\u2b50",
                callback_data=f"premium_stars:{pkg.id}",
            )
        )
    for pkg in packages:
        builder.row(
            InlineKeyboardButton(
                text=f"\U0001f4b3 {pkg.name} \u2014 {pkg.price_rub}\u20bd",
                callback_data="premium_yookassa",
            )
        )
    builder.row(
        InlineKeyboardButton(text="\u2190 Back", callback_data="my_status")
    )

    await callback.message.edit_text(
        "<b>Premium Subscription</b>\n\n"
        "\u2b50 <b>Telegram Stars</b> \u2014 instant activation\n"
        "\U0001f4b3 <b>YooKassa</b> \u2014 payment link\n\n"
        "<b>Benefits:</b>\n"
        "\u2022 Unlimited video processing\n"
        "\u2022 Priority in queue\n"
        "\u2022 Premium features",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()
