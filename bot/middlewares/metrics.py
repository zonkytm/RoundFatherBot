import functools
import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from bot.metrics import REQUEST_COUNT, REQUEST_LATENCY


class MetricsMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        fn = handler.func if isinstance(handler, functools.partial) else handler
        handler_name = getattr(fn, "__qualname__", getattr(fn, "__name__", "unknown"))
        msg_type = "text" if event.text else "photo" if event.photo else "video" if event.video else "other"

        REQUEST_COUNT.labels(handler=handler_name, message_type=msg_type).inc()

        start = time.perf_counter()
        try:
            return await handler(event, data)
        finally:
            elapsed = time.perf_counter() - start
            REQUEST_LATENCY.labels(handler=handler_name).observe(elapsed)
