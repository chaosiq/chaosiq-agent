import os
# import yaml
import shlex
import subprocess
import tempfile

from kubernetes_asyncio import config
# from kubernetes_asyncio.client.api_client import ApiClient
from kubernetes_asyncio.config.kube_config import Configuration
# from kubernetes_asyncio.utils import create_from_yaml

from ..ctk import get_chaostoolkit_settings
from ..types import Config, Job
from .base import BaseBackend

__all__ = ["K8SBackend"]


K8S_TEMPLATES = os.path.join(os.path.dirname(__file__), "../templates/k8s")


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
        settings = get_chaostoolkit_settings(
            self.config, job.access_token,
            org_id=job.org_id, team_id=job.team_id)

        secret = render_secret_manifest(settings)
        experiment = render_experiment_manifest(
            job, verify_tls=self.config.verify_tls)

        # first draft - we apply using Kubectl on command line
        for manifest in [secret, experiment]:
            with tempfile.NamedTemporaryFile(mode="w") as f:
                f.write(manifest)
                f.seek(0)

                cmd = f"kubectl apply -f {f.name}"
                p = subprocess.run(shlex.split(cmd))
                p.check_returncode()

        # with ApiClient(configuration=self.k8s_config) as api:
        #     v1 = client.CoreV1Api(api)
        #     print("Listing pods with their IPs:")
        #     ret = await v1.list_pod_for_all_namespaces()
        #     for i in ret.items:
        #         print(i.status.pod_ip, i.metadata.namespace, i.metadata.name)

        # with ApiClient(configuration=self.k8s_config) as k8s_client:
        #     for manifest in [secret, experiment]:
        #         with tempfile.NamedTemporaryFile(mode="w") as f:
        #             f.write(manifest)
        #             f.seek(0)
        #             await create_from_yaml(k8s_client, f.name,
        #                                    verbose=True, async_req=True)


###############################################################################
# Internals
###############################################################################

def render_experiment_manifest(job: Job, verify_tls: bool = True) -> str:
    with open(os.path.join(K8S_TEMPLATES, "experiment.yaml")) as f:
        template = f.read()
        experiment = template.format(
            name=job.id,  # we use the Job ID as the experiment name !
            chaos_cmd="verify" if job.target_type == "verification" else "run",
            asset_url=job.target_url,
            no_verify_tls='--no-verif-tls' if not verify_tls else '',
        )
        return experiment


# def render_secret_manifest(settings: str) -> str:
#     """
#     We load both settings & secret manifest as YAML, so that we can easily
#     inject the multi-lines settings into the secret manifest
#     """
#     with open(os.path.join(K8S_TEMPLATES, "secret.yaml")) as f:
#         template = f.read()
#         secret = yaml.safe_load(template)
#         secret['stringData']['settings.yaml'] = yaml.safe_load(settings)
#         secret = yaml.safe_dump(secret)
#         return secret


def render_secret_manifest(settings: str) -> str:
    """
    We need to keep the settings as a multi-line string content
    so that the K8s secret can base64 encode it on creation/update
    """
    with open(os.path.join(K8S_TEMPLATES, "secret.yaml")) as f:
        template = f.read()
        secret = template.format(settings=_indent_settings(settings))
        return secret


def _indent_settings(settings: str, indent: int = 4) -> str:
    spaces = ' ' * indent
    lines = settings.split(os.linesep)
    lines = [f"{spaces}{line}" for line in lines]
    return str(os.linesep.join(lines))
