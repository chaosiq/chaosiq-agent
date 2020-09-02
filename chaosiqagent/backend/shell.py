import os
import shlex
import subprocess
import tempfile

from ..types import Config, Job
from .base import BaseBackend
from ..ctk import get_chaostoolkit_settings
from ..log import logger

__all__ = ["ShellBackend"]


class ShellBackend(BaseBackend):
    def __init__(self, config: Config) -> None:
        BaseBackend.__init__(self, config)
        self.bin = self.config.chaos_binary

    async def setup(self) -> None:
        # ensure the `chaos` binary path is defined & exists
        if not self.bin:
            logger.critical("'chaos' binary path must be set in config!")
            return

        if not os.path.exists(self.bin):
            logger.critical("'chaos' binary path cannot be found, "
                            "please check your config!")
            return

        logger.info(f"Backend '{self.name}' configured with "
                    f"Chaos Toolkit binary: {self.bin}")

    async def cleanup(self) -> None:
        self.bin = None

    async def process_job(self, job: Job) -> None:
        """
        Uses the Chaos Toolkit's `chaos` command on the local shell
        to run the experiments.
        """
        settings = get_chaostoolkit_settings(
            self.config, job.access_token,
            org_id=job.org_id, team_id=job.team_id)

        with tempfile.NamedTemporaryFile(mode="w") as f:
            f.write(settings)
            f.seek(0)

            # full_cmd = f"{self.bin} --settings {f.name} info settings"
            cmd = "verify" if job.target_type == "verification" else "run"
            full_cmd = f"{self.bin} --settings {f.name} {cmd} {job.target_url}"

            # handle no verify TLS option
            if not self.config.verify_tls:
                full_cmd = f"{full_cmd} --no-verify-tls"

            p = subprocess.run(shlex.split(full_cmd))
            p.check_returncode()
