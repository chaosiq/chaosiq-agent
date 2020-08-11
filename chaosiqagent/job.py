import asyncio
import json
from types import TracebackType
from typing import Any, Dict, Optional, Type

import aiojobs
from aiojobs import Scheduler
from httpx import AsyncClient
from pydantic import ValidationError

from .backend import BaseBackend
from .log import logger
from .types import Config, Job

__all__ = ["Jobs"]


class Jobs:
    def __init__(self, config: Config, backend: BaseBackend) -> None:
        self.sched: Scheduler = None
        self.config = config
        self.backend = backend
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

        base_url = self.config.agent_url
        url = f"{base_url}/api/v1/jobs"
        access_token = self.config.agent_access_token
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        self._running = True
        while self.running and not self.sched.closed:
            await asyncio.sleep(0.3)

            async with AsyncClient() as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
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
        self._running = False

    async def handle_job(self, job: Job) -> None:
        await self.sched.spawn(self.backend.process_job(job=job))
