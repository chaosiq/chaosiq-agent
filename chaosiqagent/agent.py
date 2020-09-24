import asyncio
import httpcore
import httpx
import signal

from . import __version__ as version
from .backend import get_backend
from .client import get_client
from .job import Jobs
from .heartbeat import Heartbeat
from .log import logger
from .types import Config
from .utils import raise_if_errored

__all__ = ["Agent"]


class Agent:
    def __init__(self, config: Config) -> None:
        self.client = get_client(config)
        self.backend = get_backend(config)
        self.jobs = Jobs(config, self.backend)
        self._running = False
        self.action_url = "/agent/actions"
        self.heartbeat = Heartbeat(config)

    @property
    def running(self) -> bool:
        return self._running

    async def setup(self) -> None:
        futures = await asyncio.wait([
            self.register(),
            self.connect(),
            self.jobs.setup(),
            self.backend.setup(),
            self.heartbeat.setup(),
        ], return_when=asyncio.ALL_COMPLETED)
        raise_if_errored(*futures)

    async def cleanup(self) -> None:
        """
        Gracefully cleaning up the jobs consumer and its backend.
        """
        futures = await asyncio.wait([
            self.disconnect(),
            self.jobs.cleanup(),
            self.backend.cleanup(),
            self.heartbeat.cleanup(),
        ], return_when=asyncio.ALL_COMPLETED)
        self._running = False
        raise_if_errored(*futures)

    async def run(self) -> None:
        logger.info("Starting agent...")
        await self.setup()
        logger.info("Agent components configured")

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

    async def register(self) -> None:
        """
        Registers the agent to ChaosIQ
        """
        body = {
            "action": "register",
            "payload": {
                "type": self.backend.name,
                "version": f"{version}",
                "meta": {}
            },
        }
        try:
            await self.client.post(self.action_url, json=body)
        except (httpx.HTTPError, httpcore.ConnectError):
            logger.critical("Agent was not able to register to ChaosIQ.")
            logger.warning(
                "Agent will not work properly if not connected to ChaosIQ.")

    async def connect(self) -> None:
        """
        Indicate the agent is connected to ChaosIQ.
        It can now receive jobs.
        """
        await self.client.post(self.action_url, json={"action": "connect"})

    async def disconnect(self) -> None:
        """
        Indicate the agent is disconnected from ChaosIQ.
        It cannot be used anymore for running jobs.
        """
        await self.client.post(self.action_url, json={"action": "disconnect"})
