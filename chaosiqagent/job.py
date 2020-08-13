import asyncio
import json
from types import TracebackType
from typing import Optional, Type

import aiojobs
from aiojobs import Scheduler
from pydantic import ValidationError

from .backend import BaseBackend
from .client import get_client
from .log import logger
from .types import Config, Job

__all__ = ["Jobs"]


class Jobs:
    def __init__(self, config: Config, backend: BaseBackend) -> None:
        self.sched: Scheduler = None
        self.config = config
        self.backend = backend
        self.client = get_client(config)
        self._running = False

    async def __aenter__(self) -> 'Jobs':
        await self.setup()
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]],
                        exc_value: Optional[BaseException],
                        traceback: Optional[TracebackType]) -> None:
        await self.cleanup()

    @property
    def running(self) -> bool:
        """
        Flag that is set when the jobs are being consumed.
        """
        return self._running

    async def setup(self) -> None:
        """
        Create the underlying scheduler to handle jobs.
        """
        logger.info("Creating job consumer queue")
        self.sched = await asyncio.wait_for(aiojobs.create_scheduler(), None)

    async def cleanup(self) -> None:
        """
        Gracefully terminate the scheduler.
        """
        if not self.sched.closed:
            logger.info("Closing job consumer queue")
            await asyncio.wait_for(self.sched.close(), None)

    async def consume(self) -> None:
        """
        Consume jobs.
        """
        logger.info("Consuming jobs...")

        url = "/agent/jobs/queue/next"
        self._running = True
        while self.running and not self.sched.closed:

            async with self.client as client:
                resp = await client.get(url)
                if resp.status_code == 204:
                    # wait when queue is empty
                    await asyncio.sleep(5)
                    continue

                if resp.status_code >= 400:
                    logger.info(
                        f"Failed to fetch jobs from ChaosIQ: {resp.text}")
                    continue

                try:
                    body = resp.json()
                except json.JSONDecodeError:
                    logger.error(
                        f"Failed to decode ChaosIQ's response {resp.text}",
                        exc_info=True)
                    continue

                try:
                    job = Job.parse_obj(body)
                except ValidationError as x:
                    logger.error(f"Failed to parse job: {str(x)}")
                    continue

                await self.handle_job(job)
                await self.ack_job(job)

            # wait between jobs to allow other functions to execute (needed ??)
            await asyncio.sleep(0.3)

        self._running = False

    async def handle_job(self, job: Job) -> None:
        await self.sched.spawn(self.backend.process_job(job=job))

    async def ack_job(self, job: Job) -> None:
        """
        This ACK is to remove the processed job from the job queue
        """
        async with self.client as client:
            await client.delete(f"/agent/jobs/queue/{job.id}")
