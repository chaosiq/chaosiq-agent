from ..types import Config, Job
from .base import BaseBackend

__all__ = ["ShellBackend"]


class ShellBackend(BaseBackend):
    def __init__(self, config: Config) -> None:
        BaseBackend.__init__(self, config)

    async def setup(self) -> None:
        raise NotImplementedError()

    async def cleanup(self) -> None:
        raise NotImplementedError()

    async def process_job(self, job: Job) -> None:
        """
        Uses the Chaos Toolkit's `chaos` command on the local shell
        to run the experiments.
        """
        raise NotImplementedError()
