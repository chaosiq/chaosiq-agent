# type: ignore
import asyncio
from asyncio import AbstractEventLoop
import os
import signal
import threading
import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from chaosiqagent.agent import Agent
from chaosiqagent.log import configure_logging
from chaosiqagent.settings import load_settings


@patch("chaosiqagent.job.AsyncClient", autospec=True)
def test_agent_gracefully_terminates_on_SIGINT(httpx: httpx.AsyncClient,
                                               http_test_client: httpx.AsyncClient,
                                               config_path: str):
    def _send_signal():
        time.sleep(0.5)
        os.kill(os.getpid(), signal.SIGINT)

    thread = threading.Thread(target=_send_signal, daemon=True)
    thread.start()

    httpx.return_value = http_test_client
    c = load_settings(config_path)

    agent = Agent(c)
    asyncio.run(agent.run(), debug=True)
    assert agent.running == False
    httpx.assert_called()



@patch("chaosiqagent.job.AsyncClient", autospec=True)
def test_agent_gracefully_terminates_on_SIGTERM(httpx: httpx.AsyncClient,
                                                http_test_client: httpx.AsyncClient,
                                                config_path: str):
    def _send_signal():
        time.sleep(0.5)
        os.kill(os.getpid(), signal.SIGTERM)

    thread = threading.Thread(target=_send_signal, daemon=True)
    thread.start()

    httpx.return_value = http_test_client
    c = load_settings(config_path)

    agent = Agent(c)
    asyncio.run(agent.run(), debug=True)
    assert agent.running == False
    httpx.assert_called()


@patch("chaosiqagent.job.AsyncClient", autospec=True)
def test_agent_gracefully_terminates_on_SIGHUP(httpx: httpx.AsyncClient,
                                               http_test_client: httpx.AsyncClient,
                                               config_path: str):
    def _send_signal():
        time.sleep(0.5)
        os.kill(os.getpid(), signal.SIGHUP)

    thread = threading.Thread(target=_send_signal, daemon=True)
    thread.start()

    httpx.return_value = http_test_client
    c = load_settings(config_path)

    agent = Agent(c)
    asyncio.run(agent.run(), debug=True)
    assert agent.running == False
    httpx.assert_called()
