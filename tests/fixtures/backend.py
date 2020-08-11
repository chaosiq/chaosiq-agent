from chaosiqagent.types import Job
from chaosiqagent.backend.base import BaseBackend
from chaosiqagent.types import Job

__all__ = ["DummyBackend"]


class DummyBackend(BaseBackend):
    async def setup(self) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    async def process_job(self, job: Job) -> None:
        pass
