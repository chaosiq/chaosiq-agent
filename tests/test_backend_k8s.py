import os
from tempfile import NamedTemporaryFile
import tempfile
from unittest.mock import patch
import uuid
import uuid
import yaml

import pytest

from chaosiqagent.agent import Agent
from chaosiqagent.settings import load_settings
from chaosiqagent.backend.k8s import render_experiment_manifest, \
    render_secret_manifest



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

        agent = Agent(c)
        assert agent.backend.__class__.__name__ == "K8SBackend"

        await agent.setup()
        assert agent.backend.k8s_config.host == "https://example.com"

        await agent.cleanup()
        assert agent.backend.k8s_config is None
        del os.environ["KUBECONFIG"]


@pytest.mark.asyncio
@patch("chaosiqagent.backend.k8s.ApiClient", autospec=True)
async def test_load_kube_config_process_job(api_client, config_path: str):
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

        agent = Agent(c)
        await agent.setup()

        job = {"id": str(uuid.uuid4())}
        await agent.backend.process_job(job)

        await agent.cleanup()
        assert agent.backend.k8s_config is None
        del os.environ["KUBECONFIG"]


def test_render_experiment_manifest(job):
    manifest = render_experiment_manifest(job=job)
    print(manifest)
    assert manifest not in [None, '']

    # ensure yaml is valid
    try:
        yaml.safe_load(manifest)
    except yaml.YAMLError as exc:
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
    print(manifest)
    assert manifest not in [None, '']

    # ensure yaml is valid
    try:
        yaml.safe_load(manifest)
    except yaml.YAMLError as exc:
        pytest.fail("manifest YAML is not valid")

    # ensure all fields have been replaced
    assert '{' not in manifest
    assert '}' not in manifest
