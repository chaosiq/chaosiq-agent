import json
from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest
import respx

from chaosiqagent.agent import Agent
from chaosiqagent.log import configure_logging
from chaosiqagent.settings import load_settings
from chaosiqagent.types import Job


@pytest.mark.asyncio
async def test_load_chaos_binary(capsys, config_path: str):
    with NamedTemporaryFile() as bin:

        with open(config_path) as o:
            with NamedTemporaryFile() as p:
                r = o.read()
                r = r.replace('AGENT_BACKEND="null"', 'AGENT_BACKEND="shell"')
                r = r.replace('CHAOS_BINARY=', f"CHAOS_BINARY={bin.name}")
                p.write(r.encode('utf-8'))
                p.seek(0)
                c = load_settings(p.name)
                configure_logging(c)

        with patch("chaosiqagent.agent.Jobs", autospec=True):
            agent = Agent(c)
            assert agent.backend.__class__.__name__ == "ShellBackend"
            async with respx.mock:
                respx.post(
                    "https://console.example.com/agent/actions",
                    content=json.dumps({})
                )

                await agent.setup()
                assert agent.backend.bin == bin.name

                captured = capsys.readouterr()
                assert \
                    "Backend 'shell' configured with " \
                    f"Chaos Toolkit binary: {bin.name}" in captured.err

                await agent.cleanup()
                assert agent.backend.bin is None


@pytest.mark.asyncio
async def test_setup_missing_chaos_binary(capsys, config_path: str):
    with open(config_path) as o:
        with NamedTemporaryFile() as p:
            r = o.read()
            r = r.replace('AGENT_BACKEND="null"', 'AGENT_BACKEND="shell"')
            p.write(r.encode('utf-8'))
            p.seek(0)
            c = load_settings(p.name)
            configure_logging(c)

        with patch("chaosiqagent.agent.Jobs", autospec=True):
            agent = Agent(c)
            assert agent.backend.__class__.__name__ == "ShellBackend"
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
                assert agent.backend.bin in [None, ""]

                captured = capsys.readouterr()
                assert "'chaos' binary path must be set in config" in captured.err
                assert "Backend 'shell' configured with " not in captured.err

                await agent.cleanup()


@pytest.mark.asyncio
async def test_setup_chaos_binary_cannot_be_found(capsys, config_path: str):
    with open(config_path) as o:
        with NamedTemporaryFile() as p:
            r = o.read()
            r = r.replace('AGENT_BACKEND="null"', 'AGENT_BACKEND="shell"')
            r = r.replace('CHAOS_BINARY=', 'CHAOS_BINARY=/usr/bin/chaos')
            p.write(r.encode('utf-8'))
            p.seek(0)
            c = load_settings(p.name)
            configure_logging(c)

        with patch("chaosiqagent.agent.Jobs", autospec=True):
            agent = Agent(c)
            assert agent.backend.__class__.__name__ == "ShellBackend"

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
                assert agent.backend.bin == '/usr/bin/chaos'

                captured = capsys.readouterr()
                assert "'chaos' binary path must be set in config" not in captured.err
                assert "'chaos' binary path cannot be found" in captured.err
                assert "Backend 'shell' configured with " not in captured.err

                await agent.cleanup()


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

            await agent.backend.process_job(verification)
            subprocess_run.assert_called()
            cmd = ' '.join(subprocess_run.call_args_list[0].args[0])
            assert "--no-verify-tls" in cmd

            await agent.cleanup()
