from aiogram import Router

from .admin import admin_router
from .premium import premium_router
from .start import start_router
from .status import status_router
from .video import video_router

handlers_router = Router()
handlers_router.include_routers(
    start_router, video_router, admin_router, premium_router, status_router
)
