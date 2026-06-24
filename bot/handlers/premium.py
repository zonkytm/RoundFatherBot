import logging
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.metrics import PREMIUM_PAYMENTS
from bot.models.base import async_session
from bot.models.premium import Payment, PremiumPackage
from bot.models.user import User

logger = logging.getLogger(__name__)

premium_router = Router()


@premium_router.message(Command("premium"))
async def cmd_premium(message: Message) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(PremiumPackage)
            .where(PremiumPackage.is_active)
            .order_by(PremiumPackage.sort_order)
        )
        packages = result.scalars().all()

    if not packages:
        await message.answer("Premium packages are not available yet.")
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

    await message.answer(
        "<b>Premium Subscription</b>\n\n"
        "\u2b50 <b>Telegram Stars</b> \u2014 instant activation\n"
        "\U0001f4b3 <b>YooKassa</b> \u2014 payment link\n\n"
        "<b>Benefits:</b>\n"
        "\u2022 Unlimited video processing\n"
        "\u2022 Priority in queue\n"
        "\u2022 Premium features",
        reply_markup=builder.as_markup(),
    )


@premium_router.callback_query(F.data.startswith("premium_stars:"))
async def callback_premium_stars(callback: CallbackQuery):
    package_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        pkg = await session.get(PremiumPackage, package_id)
        if not pkg:
            await callback.answer("Package not found.", show_alert=True)
            return

        await callback.bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Premium \u2014 {pkg.name}",
            description=f"Premium subscription for {pkg.duration_days} days",
            payload=f"premium:{package_id}:{callback.from_user.id}",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label=f"Premium {pkg.name}", amount=pkg.price_stars)],
        )
    await callback.answer()


@premium_router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


@premium_router.message(F.successful_payment)
async def on_successful_payment(message: Message) -> None:
    payment = message.successful_payment
    parts = payment.invoice_payload.split(":")
    if len(parts) != 3 or parts[0] != "premium":
        return

    package_id = int(parts[1])
    user_tg_id = int(parts[2])

    async with async_session() as session:
        pkg = await session.get(PremiumPackage, package_id)
        if not pkg:
            return

        result = await session.execute(select(User).where(User.telegram_id == user_tg_id))
        user = result.scalar_one_or_none()
        if not user:
            return

        now = datetime.utcnow()
        if user.is_premium and user.premium_expires_at and user.premium_expires_at > now:
            expires = user.premium_expires_at + timedelta(days=pkg.duration_days)
        else:
            expires = now + timedelta(days=pkg.duration_days)

        user.is_premium = True
        user.premium_expires_at = expires

        payment_record = Payment(
            user_id=user.id,
            package_id=package_id,
            amount=payment.total_amount,
            currency=payment.currency,
            payment_id=payment.telegram_payment_charge_id,
            status="completed",
        )
        session.add(payment_record)
        await session.commit()

    PREMIUM_PAYMENTS.labels(package=pkg.name, status="completed").inc()
    logger.info(
        "Payment received: user=%d, package=%s, amount=%d",
        user_tg_id,
        pkg.name,
        payment.total_amount,
    )

    await message.answer(
        f"<b>Premium activated!</b>\n\n"
        f"Package: {pkg.name}\n"
        f"Expires: {expires.strftime('%d.%m.%Y')}\n\n"
        "You now have unlimited video processing."
    )


@premium_router.callback_query(F.data == "premium_yookassa")
async def callback_premium_yookassa(callback: CallbackQuery):
    await callback.answer(
        "YooKassa payment will be available soon.\nUse \u2b50 Telegram Stars for now.",
        show_alert=True,
    )
