from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from bot.models.base import async_session
from bot.models.user import User

start_router = Router()


@start_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if user and user.is_blocked:
            user.is_blocked = False
            await session.commit()

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="\U0001f4ca My Status", callback_data="my_status"),
    )
    builder.row(
        InlineKeyboardButton(text="\u2b50 Buy Premium", callback_data="show_premium"),
    )
    builder.row(
        InlineKeyboardButton(text="\U0001f4e1 Help", callback_data="help"),
    )

    await message.answer(
        f"Hello, <b>{message.from_user.full_name}</b>!\n\n"
        "Send me a video and I will convert it to a circle video note.",
        reply_markup=builder.as_markup(),
    )
