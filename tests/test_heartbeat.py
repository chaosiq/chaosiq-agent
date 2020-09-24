# type: ignore
import json
import threading
import time

import pytest
import respx
from unittest.mock import patch, AsyncMock

from chaosiqagent.backend.base import BaseBackend
from chaosiqagent.heartbeat import Heartbeat
from chaosiqagent.job import Jobs
from chaosiqagent.json import JSONEncoder
from chaosiqagent.log import configure_logging
from chaosiqagent.settings import load_settings
from chaosiqagent.types import Job


@pytest.mark.asyncio
async def test_send_heartbeat(config_path: str):
    c = load_settings(config_path)
    c.heartbeat_interval = 1  # every second
    configure_logging(c)

    async with respx.mock:
        req_heartbeat = respx.post(
            f"https://console.example.com/agent/actions", status_code=200)

        async with Heartbeat(c) as h:

            def terminate():
                time.sleep(1.5)
                h._running = False

            thread = threading.Thread(target=terminate, daemon=True)
            thread.start()

            # need to have the send_pulse function being executed as spawn
            # NB: function is spawned by the setup method
            await h.aiojob.wait(timeout=5.0)

        assert req_heartbeat.called
        try:
            req_body = json.loads(list(req_heartbeat.calls[0][0].stream)[0])
            assert req_body["action"] == "heartbeat"
        except (AssertionError, json.JSONDecodeError, IndexError):
            assert False, "Unable to ensure heartbeat action was sent"


@pytest.mark.asyncio
async def test_setup_with_invalid_interval(capsys, config_path: str):
    c = load_settings(config_path)
    c.heartbeat_interval = 0
    configure_logging(c)

    h = Heartbeat(c)
    await h.setup()

    assert h.running is False

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Heartbeat is not properly configured" in captured.err

