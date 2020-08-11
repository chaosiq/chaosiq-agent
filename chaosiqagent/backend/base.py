from ..log import logger
from ..types import Config, Job

__all__ = ["BaseBackend", "NullBackend"]


class BaseBackend:
    def __init__(self, config: Config) -> None:
        self.config = config

    async def setup(self) -> None:
        raise NotImplementedError()

    async def cleanup(self) -> None:
        raise NotImplementedError()

    async def process_job(self, job: Job) -> None:
        raise NotImplementedError()


class NullBackend(BaseBackend):
    async def setup(self) -> None:
        logger.info("Starting 'null' backend")

    async def cleanup(self) -> None:
        logger.info("Terminating 'null' backend")

    async def process_job(self, job: Job) -> None:
        logger.info(f"NullBackend got job: {str(job)}")
