from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest

from chaosiqagent.agent import Agent
from chaosiqagent.settings import load_settings
from chaosiqagent.types import Job


@pytest.mark.asyncio
async def test_load_chaos_binary(config_path: str):

    with open(config_path) as o:
        with NamedTemporaryFile() as p:
            r = o.read()
            r = r.replace('AGENT_BACKEND="null"', 'AGENT_BACKEND="shell"')
            r = r.replace('CHAOS_BINARY=', 'CHAOS_BINARY=/usr/bin/chaos')
            p.write(r.encode('utf-8'))
            p.seek(0)
            c = load_settings(p.name)

        agent = Agent(c)
        assert agent.backend.__class__.__name__ == "ShellBackend"

        await agent.setup()
        assert agent.backend.bin == "/usr/bin/chaos"

        await agent.cleanup()
        assert agent.backend.bin is None


@pytest.mark.asyncio
@patch("subprocess.run", autospec=True)
async def test_process_job(
        subprocess_run, config_path: str, job: Job):
    with open(config_path) as o:
        with NamedTemporaryFile() as p:
            r = o.read()
            r = r.replace('AGENT_BACKEND="null"', 'AGENT_BACKEND="shell"')
            r = r.replace('CHAOS_BINARY=', 'CHAOS_BINARY=chaos')
            p.write(r.encode('utf-8'))
            p.seek(0)
            c = load_settings(p.name)

    agent = Agent(c)
    await agent.setup()

    await agent.backend.process_job(job)
    subprocess_run.assert_called()

    await agent.cleanup()


@pytest.mark.asyncio
@patch("subprocess.run", autospec=True)
async def test_process_experiment(
        subprocess_run, config_path: str, experiment: Job):
    with open(config_path) as o:
        with NamedTemporaryFile() as p:
            r = o.read()
            r = r.replace('AGENT_BACKEND="null"', 'AGENT_BACKEND="shell"')
            r = r.replace('CHAOS_BINARY=', 'CHAOS_BINARY=chaos')
            p.write(r.encode('utf-8'))
            p.seek(0)
            c = load_settings(p.name)

    agent = Agent(c)
    await agent.setup()

    await agent.backend.process_job(experiment)
    subprocess_run.assert_called()
    cmd = ' '.join(subprocess_run.call_args_list[0].args[0])
    assert "chaos" in cmd
    assert "run" in cmd
    assert "--settings" in cmd
    assert "https://console.example.com/assets/experiments/" in cmd

    await agent.cleanup()


@pytest.mark.asyncio
@patch("subprocess.run", autospec=True)
async def test_process_verification(
        subprocess_run, config_path: str, verification: Job):
    with open(config_path) as o:
        with NamedTemporaryFile() as p:
            r = o.read()
            r = r.replace('AGENT_BACKEND="null"', 'AGENT_BACKEND="shell"')
            r = r.replace('CHAOS_BINARY=', 'CHAOS_BINARY=chaos')
            p.write(r.encode('utf-8'))
            p.seek(0)
            c = load_settings(p.name)

    agent = Agent(c)
    await agent.setup()

    await agent.backend.process_job(verification)
    subprocess_run.assert_called()
    cmd = ' '.join(subprocess_run.call_args_list[0].args[0])
    assert "chaos" in cmd
    assert "verify" in cmd
    assert "--settings" in cmd
    assert "https://console.example.com/assets/verifications/" in cmd

    await agent.cleanup()


@pytest.mark.asyncio
@patch("subprocess.run", autospec=True)
async def test_process_job_without_tls(
        subprocess_run, config_path: str, verification: Job):
    # chaos binary supports an option for not checking TLS
    # when pushing its results to a local console server
    with open(config_path) as o:
        with NamedTemporaryFile() as p:
            r = o.read()
            r = r.replace('AGENT_BACKEND="null"', 'AGENT_BACKEND="shell"')
            r = r.replace('CHAOS_BINARY=', 'CHAOS_BINARY=chaos')
            r = r.replace('VERIFY_TLS=True', 'VERIFY_TLS=False')
            p.write(r.encode('utf-8'))
            p.seek(0)
            c = load_settings(p.name)

    agent = Agent(c)
    await agent.setup()

    await agent.backend.process_job(verification)
    subprocess_run.assert_called()
    cmd = ' '.join(subprocess_run.call_args_list[0].args[0])
    assert "--no-verify-tls" in cmd

    await agent.cleanup()

