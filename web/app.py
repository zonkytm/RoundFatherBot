import asyncio
import logging
from pathlib import Path

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import generate_latest
from sqlalchemy import text

from bot.config import settings
from bot.models.base import async_session
from web.routes import mailings, revenue, stats
from web.routes.auth import get_current_user
from web.routes.auth import router as auth_router
from web.routes.settings import router as settings_router

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Bot Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(auth_router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(mailings.router, prefix="/api")
app.include_router(revenue.router, prefix="/api")
app.include_router(settings_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    checks = {"db": False, "redis": False}
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
            checks["db"] = True
    except Exception as e:
        logger.warning("DB health check failed: %s", e)

    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.aclose()
        checks["redis"] = True
    except Exception as e:
        logger.warning("Redis health check failed: %s", e)

    status_code = 200 if all(checks.values()) else 503
    return JSONResponse(content={"status": "ready" if all(checks.values()) else "degraded", "checks": checks}, status_code=status_code)


@app.get("/metrics")
async def metrics():
    return PlainTextResponse(generate_latest(), media_type="text/plain")


@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})


@app.get("/")
async def dashboard(request: Request, user: dict = Depends(get_current_user)):
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "dashboard.html", {})


@app.get("/mailings")
async def mailings_page(request: Request, user: dict = Depends(get_current_user)):
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "mailings.html", {})


@app.get("/revenue")
async def revenue_page(request: Request, user: dict = Depends(get_current_user)):
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "revenue.html", {})


@app.get("/settings")
async def settings_page(request: Request, user: dict = Depends(get_current_user)):
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(request, "settings.html", {})
