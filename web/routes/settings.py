from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from bot.models.base import async_session
from bot.models.premium import PremiumPackage
from bot.models.setting import BotSetting
from web.routes.auth import require_admin

router = APIRouter(prefix="/settings", tags=["settings"])

DEFAULT_SETTINGS = [
    ("daily_limit", "10", "Daily video limit for free users"),
    ("rate_limit_per_minute", "5", "Max videos per user per minute"),
]


class SettingUpdate(BaseModel):
    value: str


class PackageUpdate(BaseModel):
    price_stars: int
    price_rub: int


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
        settings_result = await session.execute(select(BotSetting).order_by(BotSetting.key))
        settings = [
            {
                "id": s.id,
                "key": s.key,
                "value": s.value,
                "description": s.description,
                "type": "setting",
            }
            for s in settings_result.scalars().all()
        ]

        packages_result = await session.execute(
            select(PremiumPackage).order_by(PremiumPackage.sort_order)
        )
        packages = [
            {
                "id": p.id,
                "key": f"package_{p.id}",
                "name": p.name,
                "price_stars": p.price_stars,
                "price_rub": p.price_rub,
                "type": "package",
            }
            for p in packages_result.scalars().all()
        ]

    return {"settings": settings, "packages": packages}


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


@router.put("/package/{package_id}")
async def update_package(package_id: int, body: PackageUpdate, user: dict = Depends(require_admin)):
    async with async_session() as session:
        pkg = await session.get(PremiumPackage, package_id)
        if not pkg:
            return {"error": "not found"}
        pkg.price_stars = body.price_stars
        pkg.price_rub = body.price_rub
        await session.commit()
    return {
        "ok": True,
        "id": package_id,
        "price_stars": body.price_stars,
        "price_rub": body.price_rub,
    }
