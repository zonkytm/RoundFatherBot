from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from bot.models.base import async_session
from bot.models.premium import Payment, PremiumPackage
from bot.models.user import User
from web.routes.auth import require_admin

router = APIRouter(tags=["revenue"])


@router.get("/revenue")
async def api_revenue(user: dict = Depends(require_admin)):
    async with async_session() as session:
        total_stars = (
            await session.execute(
                select(func.coalesce(func.sum(Payment.amount), 0)).where(
                    Payment.currency == "stars", Payment.status == "completed"
                )
            )
        ).scalar() or 0

        total_rub = (
            await session.execute(
                select(func.coalesce(func.sum(Payment.amount), 0)).where(
                    Payment.currency == "rub", Payment.status == "completed"
                )
            )
        ).scalar() or 0

        total_payments = (
            await session.execute(
                select(func.count(Payment.id)).where(Payment.status == "completed")
            )
        ).scalar() or 0

        total_users = (await session.execute(select(func.count(User.id)))).scalar() or 0
        premium_users = (
            await session.execute(select(func.count(User.id)).where(User.is_premium))
        ).scalar() or 0

        conversion = (premium_users / total_users * 100) if total_users > 0 else 0

        return {
            "total_stars": total_stars,
            "total_rub": total_rub,
            "total_payments": total_payments,
            "total_users": total_users,
            "premium_users": premium_users,
            "conversion": round(conversion, 1),
        }


@router.get("/revenue/monthly")
async def api_revenue_monthly(user: dict = Depends(require_admin)):
    async with async_session() as session:
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        result = await session.execute(
            select(
                func.date_trunc("month", Payment.created_at).label("month"),
                Payment.currency,
                func.coalesce(func.sum(Payment.amount), 0).label("total"),
                func.count(Payment.id).label("count"),
            )
            .where(
                Payment.status == "completed",
                Payment.created_at >= six_months_ago,
            )
            .group_by("month", Payment.currency)
            .order_by("month")
        )

        monthly = {}
        for row in result:
            month_str = row.month.strftime("%Y-%m")
            if month_str not in monthly:
                monthly[month_str] = {"month": month_str, "stars": 0, "rub": 0, "count": 0}
            monthly[month_str][row.currency] = row.total
            monthly[month_str]["count"] += row.count

        return list(monthly.values())


@router.get("/revenue/packages")
async def api_revenue_packages(user: dict = Depends(require_admin)):
    async with async_session() as session:
        result = await session.execute(
            select(
                PremiumPackage.name,
                func.coalesce(func.sum(Payment.amount), 0).label("total"),
                func.count(Payment.id).label("count"),
            )
            .join(Payment, Payment.package_id == PremiumPackage.id)
            .where(Payment.status == "completed")
            .group_by(PremiumPackage.id, PremiumPackage.name)
            .order_by(PremiumPackage.sort_order)
        )

        packages = [{"name": row.name, "total": row.total, "count": row.count} for row in result]

        total = sum(p["count"] for p in packages)
        for p in packages:
            p["percentage"] = round(p["count"] / total * 100, 1) if total > 0 else 0

        return packages


@router.get("/revenue/recent")
async def api_revenue_recent(user: dict = Depends(require_admin)):
    async with async_session() as session:
        result = await session.execute(
            select(Payment).order_by(Payment.created_at.desc()).limit(20)
        )
        payments = result.scalars().all()

        enriched = []
        for p in payments:
            user_result = await session.execute(select(User).where(User.id == p.user_id))
            user_obj = user_result.scalar_one_or_none()
            pkg_result = await session.execute(
                select(PremiumPackage).where(PremiumPackage.id == p.package_id)
            )
            pkg = pkg_result.scalar_one_or_none()

            user_name = "Unknown"
            if user_obj:
                user_name = user_obj.username or user_obj.first_name or str(user_obj.telegram_id)

            enriched.append(
                {
                    "id": p.id,
                    "user": user_name,
                    "package": pkg.name if pkg else "Unknown",
                    "amount": p.amount,
                    "currency": p.currency,
                    "status": p.status,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
            )

        return enriched
