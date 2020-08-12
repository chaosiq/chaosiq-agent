import httpx

from .types import Config

__all__ = ["get_client"]


class ChaosIQClient(httpx.AsyncClient):
    def __init__(self, config: Config):

        super().__init__(
            headers={
                "Authorization": f"Bearer {config.agent_access_token}",
                "Accept": "application/json",
            },
            base_url=config.agent_url,
            verify=config.verify_tls,
            timeout=2,
        )


def get_client(config: Config) -> ChaosIQClient:
    return ChaosIQClient(config)
