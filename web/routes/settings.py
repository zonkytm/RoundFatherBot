from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from bot.models.base import async_session
from bot.models.setting import BotSetting
from web.routes.auth import get_current_user, require_admin

router = APIRouter(prefix="/settings", tags=["settings"])

DEFAULT_SETTINGS = [
    ("daily_limit", "10", "Daily video limit for free users"),
    ("rate_limit_per_minute", "5", "Max videos per user per minute"),
    ("premium_price_1mo_stars", "100", "1 month premium price in Stars"),
    ("premium_price_1mo_rub", "199", "1 month premium price in RUB"),
    ("premium_price_3mo_stars", "250", "3 months premium price in Stars"),
    ("premium_price_3mo_rub", "499", "3 months premium price in RUB"),
    ("premium_price_6mo_stars", "450", "6 months premium price in Stars"),
    ("premium_price_6mo_rub", "899", "6 months premium price in RUB"),
]


class SettingUpdate(BaseModel):
    value: str


async def get_setting(key: str) -> str:
    async with async_session() as session:
        result = await session.execute(select(BotSetting).where(BotSetting.key == key))
        setting = result.scalar_one_or_none()
        return setting.value if setting else ""


async def get_settings_dict() -> dict[str, str]:
    async with async_session() as session:
        result = await session.execute(select(BotSetting))
        return {s.key: s.value for s in result.scalars().all()}


async def seed_settings() -> None:
    async with async_session() as session:
        result = await session.execute(select(BotSetting).limit(1))
        if result.scalar_one_or_none():
            return
        for key, value, desc in DEFAULT_SETTINGS:
            session.add(BotSetting(key=key, value=value, description=desc))
        await session.commit()


@router.get("")
async def list_settings(user: dict = Depends(require_admin)):
    async with async_session() as session:
        result = await session.execute(select(BotSetting).order_by(BotSetting.key))
        settings = result.scalars().all()
    return [
        {"id": s.id, "key": s.key, "value": s.value, "description": s.description}
        for s in settings
    ]


@router.put("/{key}")
async def update_setting(key: str, body: SettingUpdate, user: dict = Depends(require_admin)):
    async with async_session() as session:
        result = await session.execute(select(BotSetting).where(BotSetting.key == key))
        setting = result.scalar_one_or_none()
        if not setting:
            return {"error": "not found"}
        setting.value = body.value
        await session.commit()
    return {"ok": True, "key": key, "value": body.value}
