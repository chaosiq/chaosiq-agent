import os
import yaml
from typing import Optional, Type, Dict, Any

from kubernetes_asyncio import config
from kubernetes_asyncio.client.api_client import ApiClient  # noqa: 0611 required by unit tests mock
from kubernetes_asyncio.client.api import core_v1_api, custom_objects_api
from kubernetes_asyncio.client.api.custom_objects_api import CustomObjectsApi

from kubernetes_asyncio.config.kube_config import Configuration

from ..ctk import get_chaostoolkit_settings
from ..types import Config, Job
from .base import BaseBackend
from ..log import logger

__all__ = ["K8SBackend"]


K8S_TEMPLATES = os.path.join(os.path.dirname(__file__), "../templates/k8s")
SETTINGS_NAME = "chaostoolkit-settings"


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
        # await self.create_default_namespaces()

    async def cleanup(self) -> None:
        self.k8s_config = None

    # async def create_default_namespaces(self) -> None:
    #     """
    #     Ensure the required namespaces are created, or do it as a fallback
    #     These namespaces shall be created upon the K8s CRD installation
    #     """
    #     k8s_client = ApiClient(configuration=self.k8s_config)
    #     v1 = core_v1_api.CoreV1Api(k8s_client)
    #
    #     ret = await v1.list_namespace()
    #     namespaces = [ns.metadata.name for ns in ret.items]
    #     for ns in ["chaostoolkit-crd", "chaostoolkit-run"]:
    #         if ns not in namespaces:
    #             namespace = render_namespace_manifest(ns)
    #             await v1.create_namespace(yaml.safe_load(namespace))
    #             logger.info(f"Kubernetes namespace '{ns}' created")

    async def process_job(self, job: Job) -> None:
        """
        Create the custom resource object that the Chaos Toolkit operator
        can consume.
        """
        settings = get_chaostoolkit_settings(
            self.config, job.access_token,
            org_id=job.org_id, team_id=job.team_id)
        settings_name = f"settings-{job.id}"

        labels = get_k8s_labels_for_job(job)
        secret = render_secret_manifest(
            settings, settings_name=settings_name, labels=labels)
        experiment = render_experiment_manifest(
            job, verify_tls=self.config.verify_tls,
            settings_name=settings_name)

        k8s_client = ApiClient(configuration=self.k8s_config)

        # create the secret containing the CTK settings
        try:
            api = core_v1_api.CoreV1Api(k8s_client)
            secret = await api.create_namespaced_secret(
                namespace="chaostoolkit-run", body=yaml.safe_load(secret))
            assert secret is not None
        except Exception:  # pragma: no cover
            logger.exception("Cannot create the secret on K8s")
            raise

        # create the experiment custom resource
        try:
            api = custom_objects_api.CustomObjectsApi(k8s_client)
            co = await api.create_namespaced_custom_object(
                # group, version, namespace, plural, body
                "chaostoolkit.org",
                "v1",
                "chaostoolkit-crd",
                "chaosexperiments",
                yaml.safe_load(experiment),
            )
            assert co is not None
        except Exception:  # pragma: no cover
            logger.exception("Cannot create the experiment on K8s")
            raise


###############################################################################
# Internals
###############################################################################

def render_experiment_manifest(
        job: Job, verify_tls: bool = True,
        settings_name: str = SETTINGS_NAME,
        ) -> str:
    with open(os.path.join(K8S_TEMPLATES, "experiment.yaml")) as f:
        template = f.read()
        labels = get_k8s_labels_for_job(job)
        experiment = template.format(
            name=job.id,  # we use the Job ID as the experiment name !
            chaos_cmd="verify" if job.target_type == "verification" else "run",
            asset_url=job.target_url,
            no_verify_tls='--no-verify-tls' if not verify_tls else '',
            settings_name=settings_name,
            **labels,
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


def render_secret_manifest(
        settings: str,
        settings_name: str = SETTINGS_NAME,
        labels: Dict[str, str] = None,
        ) -> str:
    """
    We need to keep the settings as a multi-line string content
    so that the K8s secret can base64 encode it on creation/update
    """
    with open(os.path.join(K8S_TEMPLATES, "secret.yaml")) as f:
        template = f.read()
        labels = labels or {}
        secret = template.format(
            settings=_indent_settings(settings),
            settings_name=settings_name,
            job_id=labels.get("id", ""),
            job_type=labels.get("type", "")
        )
        return secret


def _indent_settings(settings: str, indent: int = 4) -> str:
    spaces = ' ' * indent
    lines = settings.split(os.linesep)
    lines = [f"{spaces}{line}" for line in lines]
    return str(os.linesep.join(lines))


# def render_namespace_manifest(name: str) -> str:
#     with open(os.path.join(K8S_TEMPLATES, "namespace.yaml")) as f:
#         template = f.read()
#         namespace = template.format(name=name)
#         return namespace


def get_k8s_labels_for_job(job: Job) -> Dict[str, str]:
    """
    Returns the dict containing the labels
    to insert into the metadata for Kubernetes objects
    """
    return {
        "job_id": job.id,
        "job_type": job.target_type,
    }
