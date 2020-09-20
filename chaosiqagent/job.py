import asyncio
import json
from types import TracebackType
from typing import Optional, Type, Dict, Any

import aiojobs
from aiojobs import Scheduler
from pydantic import ValidationError

from .backend import BaseBackend
from .client import ChaosIQClient
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
        self.sched = await asyncio.wait_for(
            aiojobs.create_scheduler(
                exception_handler=self.aiojobs_exception), None)

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

        self._running = True
        wait = default = 0.3
        while self.running and not self.sched.closed:
            # wait between jobs to allow other functions to execute
            # NB: needs to be at top of while loop, due to multiple 'continue'
            await asyncio.sleep(wait)

            async with ChaosIQClient(self.config) as client:
                resp = await client.get("/agent/jobs/queue/next")
                if resp.status_code == 204:
                    # increase wait when queue is empty (max 5sec.)
                    wait = wait * 2
                    wait = wait if wait < 5 else 5
                    continue
                else:
                    # reset initial wait before jobs
                    wait = default

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
                logger.info(f"Got job '{job.id}' to process")
            except ValidationError as x:
                logger.error(f"Failed to parse job: {str(x)}")
                continue

            try:
                await self.handle_job(job)
            finally:
                await self.ack_job(job)

        self._running = False

    async def handle_job(self, job: Job) -> None:
        # await self.sched.spawn(self.backend.process_job(job=job))
        await self.sched.spawn(self.__handle_job(job=job))

    async def __handle_job(self, job: Job) -> None:
        try:
            await self.backend.process_job(job=job)
            await self.update_job_status(job, status="processed")
        except Exception as exc:  # noqa: 0703
            logger.error(f"Failed to handle job {job.id}", exc_info=True)
            await self.update_job_status(
                job, status="failed", info={"exception": str(exc)})

    async def ack_job(self, job: Job) -> None:
        """
        This ACK is to remove the processed job from the job queue
        """
        async with ChaosIQClient(self.config) as client:
            await client.delete(f"/agent/jobs/queue/{job.id}")

    async def update_job_status(
            self, job: Job, status: str, info: Dict[str, Any] = None) -> None:
        """
        Reports the status of the current job to ChaosIQ
        """
        async with ChaosIQClient(self.config) as client:
            await client.put(
                f"/agent/jobs/{job.id}/status",
                json={"status": status, "info": info},
            )

    @staticmethod
    def aiojobs_exception(
            scheduler: Scheduler,
            context: Dict[str, Any]) -> None:  # pragma: no cover
        logger.error(context)
