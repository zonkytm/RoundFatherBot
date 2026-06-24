from fastapi import APIRouter

from bot.services.stats import get_hourly_activity, get_stats

router = APIRouter(tags=["stats"])


@router.get("/stats")
async def api_stats():
    return await get_stats()


@router.get("/stats/hourly")
async def api_stats_hourly():
    return await get_hourly_activity()
