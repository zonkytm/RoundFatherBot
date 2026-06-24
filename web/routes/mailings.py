from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select, update

from bot.models.base import async_session
from bot.models.mailing import Mailing, MailingStatus
from bot.models.mailing_log import MailingLog
from bot.models.preset import MailingPreset

router = APIRouter(tags=["mailings"])


class MailingCreate(BaseModel):
    name: str
    text: str
    target: str = "all"
    scheduled_at: str | None = None
    cron_expression: str | None = None


class MailingUpdate(BaseModel):
    is_active: bool | None = None


class PresetCreate(BaseModel):
    name: str
    cron_expr: str


@router.get("/mailings")
async def list_mailings():
    async with async_session() as session:
        result = await session.execute(select(Mailing).order_by(Mailing.created_at.desc()))
        mailings = result.scalars().all()

        enriched = []
        for m in mailings:
            log_stats = await session.execute(
                select(
                    func.coalesce(func.sum(MailingLog.sent_count), 0).label("total_sent"),
                    func.coalesce(func.sum(MailingLog.failed_count), 0).label("total_failed"),
                ).where(MailingLog.mailing_id == m.id)
            )
            row = log_stats.one()
            enriched.append(
                {
                    "id": m.id,
                    "name": m.name,
                    "text": m.text,
                    "target": m.target,
                    "status": m.status,
                    "sent_count": row.total_sent,
                    "failed_count": row.total_failed,
                    "sent_at": m.sent_at.isoformat() if m.sent_at else None,
                    "scheduled_at": m.scheduled_at.isoformat() if m.scheduled_at else None,
                    "cron_expression": m.cron_expression,
                    "is_active": m.is_active,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
            )
        return enriched


@router.get("/mailings/{mailing_id}/logs")
async def mailing_logs(mailing_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(MailingLog)
            .where(MailingLog.mailing_id == mailing_id)
            .order_by(MailingLog.sent_at.desc())
        )
        logs = result.scalars().all()
        return [
            {
                "id": log.id,
                "sent_count": log.sent_count,
                "failed_count": log.failed_count,
                "sent_at": log.sent_at.isoformat() if log.sent_at else None,
            }
            for log in logs
        ]


@router.post("/mailings")
async def create_mailing(data: MailingCreate):
    scheduled_at = None
    if data.scheduled_at:
        scheduled_at = datetime.fromisoformat(data.scheduled_at)

    status = MailingStatus.PENDING
    if scheduled_at and scheduled_at > datetime.utcnow():
        status = MailingStatus.PENDING

    async with async_session() as session:
        mailing = Mailing(
            name=data.name,
            text=data.text,
            target=data.target,
            status=status,
            scheduled_at=scheduled_at,
            cron_expression=data.cron_expression,
            is_active=True,
        )
        session.add(mailing)
        await session.commit()
        await session.refresh(mailing)
        return {"id": mailing.id, "status": "created"}


@router.post("/mailings/{mailing_id}/send")
async def send_mailing(mailing_id: int):
    async with async_session() as session:
        mailing = await session.get(Mailing, mailing_id)
        if not mailing:
            raise HTTPException(status_code=404, detail="Mailing not found")
        if mailing.status == MailingStatus.SENDING:
            raise HTTPException(status_code=400, detail="Already sending")
        await session.execute(
            update(Mailing)
            .where(Mailing.id == mailing_id)
            .values(
                status=MailingStatus.PENDING,
                sent_count=0,
                failed_count=0,
                scheduled_at=None,
            )
        )
        await session.commit()
        return {"status": "queued"}


@router.patch("/mailings/{mailing_id}")
async def update_mailing(mailing_id: int, data: MailingUpdate):
    async with async_session() as session:
        mailing = await session.get(Mailing, mailing_id)
        if not mailing:
            raise HTTPException(status_code=404, detail="Mailing not found")
        if data.is_active is not None:
            mailing.is_active = data.is_active
        await session.commit()
        return {"status": "updated"}


@router.delete("/mailings/{mailing_id}")
async def delete_mailing(mailing_id: int):
    async with async_session() as session:
        mailing = await session.get(Mailing, mailing_id)
        if not mailing:
            raise HTTPException(status_code=404, detail="Mailing not found")
        if mailing.status == MailingStatus.SENDING:
            raise HTTPException(status_code=400, detail="Cannot delete while sending")
        await session.delete(mailing)
        await session.commit()
        return {"status": "deleted"}


@router.get("/presets")
async def list_presets():
    async with async_session() as session:
        result = await session.execute(
            select(MailingPreset).where(MailingPreset.is_active).order_by(MailingPreset.sort_order)
        )
        presets = result.scalars().all()
        return [{"id": p.id, "name": p.name, "cron_expr": p.cron_expr} for p in presets]


@router.post("/presets")
async def create_preset(data: PresetCreate):
    async with async_session() as session:
        max_order = await session.execute(
            select(MailingPreset.sort_order).order_by(MailingPreset.sort_order.desc()).limit(1)
        )
        next_order = (max_order.scalar_one() or 0) + 1
        preset = MailingPreset(name=data.name, cron_expr=data.cron_expr, sort_order=next_order)
        session.add(preset)
        await session.commit()
        await session.refresh(preset)
        return {"id": preset.id, "status": "created"}


@router.delete("/presets/{preset_id}")
async def delete_preset(preset_id: int):
    async with async_session() as session:
        preset = await session.get(MailingPreset, preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail="Preset not found")
        await session.delete(preset)
        await session.commit()
        return {"status": "deleted"}
