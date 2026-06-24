from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from bot.config import settings
from bot.models.base import async_session
from bot.models.user import User

admin_router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


@admin_router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Access denied.")
        return

    from bot.services.stats import get_stats

    stats = await get_stats()

    await message.answer(
        f"<b>Bot Statistics</b>\n\n"
        f"Videos processed: <b>{stats['total_videos']}</b> (24h: {stats['videos_24h']})\n"
        f"Users: <b>{stats['total_users']}</b> (24h: {stats['users_24h']})\n"
        f"Blocked: <b>{stats['blocked_users']}</b>\n"
        f"Avg processing: <b>{stats['avg_time_ms'] / 1000:.1f}s</b>\n"
        f"Errors: <b>{stats['errors']}</b>",
    )


@admin_router.message(Command("unblock"))
async def cmd_unblock(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Access denied.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Usage: /unblock <user_id>")
        return

    try:
        target_id = int(args[1])
    except ValueError:
        await message.answer("Invalid user ID.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == target_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer(f"User {target_id} not found.")
            return
        if not user.is_blocked:
            await message.answer(f"User {target_id} is not blocked.")
            return

        user.is_blocked = False
        await session.commit()
        await message.answer(f"User {target_id} unblocked.")


@admin_router.message(Command("blocked"))
async def cmd_blocked(message: Message) -> None:
    if not is_admin(message.from_user.id):
        await message.answer("Access denied.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.is_blocked)
        )
        users = result.scalars().all()

    if not users:
        await message.answer("No blocked users.")
        return

    lines = [f"<b>Blocked users ({len(users)}):</b>\n"]
    for u in users[:20]:
        name = u.username or u.first_name or str(u.telegram_id)
        lines.append(f"  \u2022 {name} (id: {u.telegram_id})")
    if len(users) > 20:
        lines.append(f"  ... and {len(users) - 20} more")

    await message.answer("\n".join(lines))
