# type: ignore
import asyncio
from asyncio import AbstractEventLoop
import json
import os
import signal
import threading
import time

import httpx
import pytest
import respx

from chaosiqagent.agent import Agent
from chaosiqagent.log import configure_logging
from chaosiqagent.settings import load_settings

@pytest.mark.skip("This unit test does not work inside docker image")
@respx.mock
@pytest.mark.parametrize('sig', [signal.SIGTERM, signal.SIGINT, signal.SIGHUP])
def test_agent_gracefully_terminates_on_signal(
        config_path: str, sig):

    def _send_signal():
        time.sleep(0.5)
        os.kill(os.getpid(), sig)

    thread = threading.Thread(target=_send_signal, daemon=True)
    thread.start()

    c = load_settings(config_path)

    req_actions = respx.post(
        "https://console.example.com/agent/actions",
        status_code=200
    )
    req_jobs = respx.get(
        "https://console.example.com/agent/jobs/queue/next",
        status_code=204
    )

    agent = Agent(c)
    asyncio.run(agent.run(), debug=True)
    assert agent.running is False
    assert req_jobs.called is True

    assert req_actions.called is True
    actions = []
    for request, response in req_actions.calls:
        req_body = json.loads(request.read())
        actions.append(req_body["action"])
    assert set(actions) == set(["register", "connect", "disconnect"])


@respx.mock
@pytest.mark.asyncio
async def test_agent_fails_connecting(config_path: str):
    c = load_settings(config_path)

    respx.post(
        "https://console.example.com/agent/actions",
        content=httpx.HTTPError("BOOOM", request=None)
    )

    agent = Agent(c)
    await agent.register()
