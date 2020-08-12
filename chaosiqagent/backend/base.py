from ..log import logger
from ..types import Config, Job, Backend

__all__ = ["BaseBackend", "NullBackend"]


class BaseBackend:
    def __init__(self, config: Config) -> None:
        self.config = config

    @property
    def name(self) -> Backend:
        return self.config.agent_backend

    async def setup(self) -> None:
        raise NotImplementedError()

    async def cleanup(self) -> None:
        raise NotImplementedError()

    async def process_job(self, job: Job) -> None:
        raise NotImplementedError()


class NullBackend(BaseBackend):
    async def setup(self) -> None:
        logger.info(f"Starting '{self.name}' backend")

    async def cleanup(self) -> None:
        logger.info(f"Terminating '{self.name}' backend")

    async def process_job(self, job: Job) -> None:
        logger.info(f"Backend '{self.name}' got job: {str(job)}")
