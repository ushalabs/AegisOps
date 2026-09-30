import asyncio
import logging

from app.core.config import settings
from app.incidents.manager import run_detection_cycle


logger = logging.getLogger(__name__)


async def incident_detection_worker():
    while True:
        try:
            await asyncio.to_thread(run_detection_cycle)

        except Exception:
            logger.exception(
                "Incident detection cycle failed"
            )

        await asyncio.sleep(
            settings.incident_detection_interval_seconds
        )