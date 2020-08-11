import asyncio
import signal

from .backend import get_backend
from .job import Jobs
from .log import logger
from .types import Config

__all__ = ["Agent"]


class Agent:
    def __init__(self, config: Config) -> None:
        self.backend = get_backend(config)
        self.jobs = Jobs(config, self.backend)
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    async def setup(self) -> None:
        await asyncio.wait([
            self.jobs.setup(),
            self.backend.setup()
        ], return_when=asyncio.ALL_COMPLETED)

    async def cleanup(self) -> None:
        """
        Gracefully cleaning up the jobs consumer and its backend.
        """
        await asyncio.wait([
            self.jobs.cleanup(),
            self.backend.cleanup()
        ], return_when=asyncio.ALL_COMPLETED)
        self._running = False

    async def run(self) -> None:
        logger.info("Starting agent...")
        await self.setup()

        # handle SIG* as gracefully as we can so that jobs are cleanly
        # cancelled
        loop = asyncio.get_running_loop()
        signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        for s in signals:
            loop.add_signal_handler(
                s, lambda s=s: asyncio.create_task(self.terminate()))

        logger.info("Agent ready to consume jobs...")
        self._running = True
        await self.jobs.consume()

    async def terminate(self) -> None:
        logger.info("Terminating agent...")
        await self.cleanup()
