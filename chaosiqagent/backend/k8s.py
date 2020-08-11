import os

from kubernetes_asyncio import config
from kubernetes_asyncio.client.api_client import ApiClient
from kubernetes_asyncio.config.kube_config import Configuration
# from kubernetes_asyncio.utils import create_from_yaml

from ..types import Config, Job
from .base import BaseBackend

__all__ = ["K8SBackend"]


class K8SBackend(BaseBackend):
    def __init__(self, config: Config) -> None:
        BaseBackend.__init__(self, config)

        # we keep our own config for kubernetes rather than use their default
        # global one as it prevents weird side effects
        self.k8s_config = Configuration()

    async def setup(self) -> None:
        await config.load_kube_config(
            config_file=os.environ.get('KUBECONFIG', '~/.kube/config'),
            client_configuration=self.k8s_config,
            persist_config=False)

    async def cleanup(self) -> None:
        self.k8s_config = None

    async def process_job(self, job: Job) -> None:
        """
        Create the custom resource object that the Chaos Toolkit operator
        can consume.
        """
        async with ApiClient(configuration=self.k8s_config):  # as api
            # await api.create_from_yaml()
            pass
