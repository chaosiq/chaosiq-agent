import json
import os
from tempfile import NamedTemporaryFile
from unittest.mock import patch, AsyncMock
import yaml

import pytest
import respx

from chaosiqagent.agent import Agent
from chaosiqagent.settings import load_settings
from chaosiqagent.backend.k8s import render_experiment_manifest, \
    render_secret_manifest
from chaosiqagent.types import Job
from chaosiqagent.backend.k8s import core_v1_api, custom_objects_api



BASIC_CONFIG = b"""
apiVersion: v1
kind: Config
preferences: {}

clusters:
- cluster:
    server: https://example.com
    certificate-authority-data: dGVzdAoK
  name: development

users:
- name: developer
  user:
    password: dGVzdHBhc3MK
    username: admin

contexts:
- context:
    cluster: development
    user: developer
  name: dev

current-context: dev
"""


@pytest.mark.asyncio
async def test_fails_when_kubeconfig_cannot_be_found(config_path: str):
    with NamedTemporaryFile() as f:
        f.write(BASIC_CONFIG)
        f.seek(0)
        os.environ["KUBECONFIG"] = "/tmp/somewhere"

        with open(config_path) as o:
            with NamedTemporaryFile() as p:
                r = o.read()
                r = r.replace("null", "kubernetes")
                p.write(r.encode('utf-8'))
                p.seek(0)
                c = load_settings(p.name)

        with patch("chaosiqagent.agent.Jobs", autospec=True):
            agent = Agent(c)
            assert agent.backend.__class__.__name__ == "K8SBackend"

            async with respx.mock:
                respx.post(
                    "https://console.example.com/agent/actions",
                    content=json.dumps({})
                )

                respx.post(
                    "https://console.example.com/agent/actions",
                    content=json.dumps({})
                )

                with pytest.raises(RuntimeError):
                    await agent.setup()
        del os.environ["KUBECONFIG"]



@pytest.mark.asyncio
async def test_load_kube_config_at_default_location(config_path: str):
    with NamedTemporaryFile() as f:
        f.write(BASIC_CONFIG)
        f.seek(0)
        os.environ["KUBECONFIG"] = f.name

        with open(config_path) as o:
            with NamedTemporaryFile() as p:
                r = o.read()
                r = r.replace("null", "kubernetes")
                p.write(r.encode('utf-8'))
                p.seek(0)
                c = load_settings(p.name)

        with patch("chaosiqagent.agent.Jobs", autospec=True):
            agent = Agent(c)
            assert agent.backend.__class__.__name__ == "K8SBackend"

            async with respx.mock:
                respx.post(
                    "https://console.example.com/agent/actions",
                    content=json.dumps({})
                )

                respx.post(
                    "https://console.example.com/agent/actions",
                    content=json.dumps({})
                )

                await agent.setup()
                assert agent.backend.k8s_config.host == "https://example.com"

                await agent.cleanup()
                assert agent.backend.k8s_config is None
            del os.environ["KUBECONFIG"]



@patch.object(custom_objects_api.CustomObjectsApi, "create_namespaced_custom_object", new_callable=AsyncMock)
@patch.object(core_v1_api.CoreV1Api, "create_namespaced_secret", new_callable=AsyncMock)
@patch("chaosiqagent.backend.k8s.ApiClient", autospec=True)
@pytest.mark.asyncio
async def test_load_kube_config_process_job(
        k8s_client, create_secret, create_custom_object,
        config_path: str, job: Job):

    with NamedTemporaryFile() as f:
        f.write(BASIC_CONFIG)
        f.seek(0)
        os.environ["KUBECONFIG"] = f.name

        with open(config_path) as o:
            with NamedTemporaryFile() as p:
                r = o.read()
                r = r.replace("null", "kubernetes")
                p.write(r.encode('utf-8'))
                p.seek(0)
                c = load_settings(p.name)

        with patch("chaosiqagent.agent.Jobs", autospec=True):
            agent = Agent(c)

            async with respx.mock:
                respx.post(
                    "https://console.example.com/agent/actions",
                    content=json.dumps({})
                )

                respx.post(
                    "https://console.example.com/agent/actions",
                    content=json.dumps({})
                )

                await agent.setup()

                await agent.backend.process_job(job)
                k8s_client.assert_called()
                create_secret.assert_awaited()
                assert create_secret.call_count == 1
                create_custom_object.assert_awaited()
                assert create_custom_object.call_count == 1

                await agent.cleanup()
                assert agent.backend.k8s_config is None
        del os.environ["KUBECONFIG"]


def test_render_experiment_manifest(job):
    manifest = render_experiment_manifest(job=job)
    assert manifest not in [None, '']

    # ensure yaml is valid
    try:
        yaml.safe_load(manifest)
    except yaml.YAMLError:
        pytest.fail("manifest YAML is not valid")

    # ensure all fields have been replaced
    assert '{' not in manifest
    assert '}' not in manifest


DUMMY_SETTINGS = """
controls:
  chaosiq-cloud:
    features:
      publish: 'on'
      safeguards: 'on'
      workspace: 'on'
"""


def test_render_secret_manifest():
    manifest = render_secret_manifest(settings=DUMMY_SETTINGS)
    assert manifest not in [None, '']

    # ensure yaml is valid
    try:
        yaml.safe_load(manifest)
    except yaml.YAMLError as exc:
        pytest.fail("manifest YAML is not valid")

    # ensure all fields have been replaced
    assert '{' not in manifest
    assert '}' not in manifest
