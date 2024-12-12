import asyncio
from datetime import datetime

from torrent_worker_coordinator.log import make_logger

log = make_logger(__name__)


async def _background_iteration() -> None:
    """Single iteration of background processing."""
    try:
        log.debug("Background task iteration at %s", datetime.now().isoformat())
        # TODO: Add actual background processing logic here
    except Exception as e:
        log.error("Error in background task: %s", str(e))


async def task_background(interval_seconds: int = 60) -> None:
    """Run background task periodically.

    Args:
        interval_seconds: Time between iterations in seconds
    """
    log.info("Starting background task with %d second interval", interval_seconds)
    while True:
        await _background_iteration()
        await asyncio.sleep(interval_seconds)
