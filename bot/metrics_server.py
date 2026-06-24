import asyncio
import logging
from functools import partial

from prometheus_client import start_http_server

logger = logging.getLogger(__name__)

_server = None


async def start_metrics_server(port: int = 9090) -> None:
    global _server
    loop = asyncio.get_event_loop()
    _server = await loop.run_in_executor(None, partial(start_http_server, port))
    logger.info("Prometheus metrics server started on port %d", port)


async def stop_metrics_server() -> None:
    global _server
    if _server:
        _server.stop()
        logger.info("Prometheus metrics server stopped")
