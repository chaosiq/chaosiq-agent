import os
import uuid
from urllib.parse import urlparse

from .types import Config


__all__ = ["get_chaostoolkit_settings"]


SETTINGS_PATH = os.path.join(
    os.path.dirname(__file__), "templates/ctk/settings.yaml")


def get_chaostoolkit_settings(
        config: Config, token: str,
        org_id: str = None, team_id: str = None,
        ) -> str:

    with open(SETTINGS_PATH) as f:
        template = f.read()

        # generates random UUIDs for org & team IDs
        # The experiment/verification once downloaded will contain those IDs
        if not org_id:
            org_id = str(uuid.uuid4())
        if not team_id:
            team_id = str(uuid.uuid4())

        parsed = urlparse(config.agent_url)
        console_url = f"{parsed.scheme}://{parsed.netloc}"
        console_hostname = parsed.netloc
        settings = template.format(
            token=token,
            org_id=org_id,
            team_id=team_id,
            console_hostname=console_hostname,
            console_url=console_url,
            verify_tls=str(config.verify_tls).lower()
        )
        return settings
