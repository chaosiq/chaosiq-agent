import asyncio
import contextlib
from types import TracebackType
from typing import Optional, Type, Dict, Any

import aiojobs
from aiojobs import Scheduler

from .client import ChaosIQClient
from .log import logger
from .types import Config


__all__ = ["Heartbeat"]


class Heartbeat:
    def __init__(self, config: Config) -> None:
        self.sched: Scheduler = None
        self.config = config
        self._running = False
        self.aiojob = None

    async def __aenter__(self) -> 'Heartbeat':
        await self.setup()
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]],
                        exc_value: Optional[BaseException],
                        traceback: Optional[TracebackType]) -> None:
        await self.cleanup()

    @property
    def running(self) -> bool:
        """
        Flag that is set when the heartbeat is active.
        """
        return self._running

    async def setup(self) -> None:
        """
        Create the underlying scheduler to periodically send the heartbeat.
        """
        logger.info("Creating heartbeat loop")
        self.sched = await asyncio.wait_for(
            aiojobs.create_scheduler(
                exception_handler=self.aiojobs_exception), None)

        period = self.config.heartbeat_interval
        if not period:
            logger.critical(f"Heartbeat is not properly configured; "
                            f"interval '{period}' is not valid")
            return

        logger.info("Spawning the heartbeat...")
        self.aiojob = await self.sched.spawn(self.send_pulse())

    async def cleanup(self) -> None:
        """
        Gracefully terminate the scheduler.
        """
        if self.aiojob:
            logger.info("Stopping heartbeat pulse...")
            await self.aiojob.close()

        if not self.sched.closed:
            logger.info("Closing heartbeat loop")
            await asyncio.wait_for(self.sched.close(), None)

        self._running = False

    async def send_pulse(self) -> None:
        """
        Sends its heartbeat periodically to the console

        This must be interrupted instantly and not until wait is complete !!
        We can NOT wait for end of iddle before leaving the loop
        """
        self._running = True
        wait = self.config.heartbeat_interval
        logger.info(f"Sending heartbeat every {wait} seconds")

        while self._running and not self.sched.closed:
            await asyncio.sleep(wait)

            with contextlib.suppress(Exception):
                async with ChaosIQClient(self.config) as client:
                    await client.post(
                        "/agent/actions", json={"action": "heartbeat"})

    @staticmethod
    def aiojobs_exception(
            scheduler: Scheduler,
            context: Dict[str, Any]) -> None:  # pragma: no cover
        logger.error(context)
