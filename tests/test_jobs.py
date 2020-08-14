# type: ignore
import json
import os
import signal
import threading
import time
import uuid

import pytest
import respx

from chaosiqagent.backend.base import BaseBackend
from chaosiqagent.job import Jobs
from chaosiqagent.log import configure_logging
from chaosiqagent.settings import load_settings


@pytest.mark.asyncio
async def test_consume_jobs(config_path: str, backend: BaseBackend):
    c = load_settings(config_path)
    configure_logging(c)
    async with Jobs(c, backend) as j:
        def terminate():
            time.sleep(0.5)
            j._running = False

        thread = threading.Thread(target=terminate, daemon=True)
        thread.start()

        async with respx.mock:
            respx.get(
                "https://console.example.com/agent/jobs/queue/next",
                content=json.dumps({"id": str(uuid.uuid4())})
            )
            await j.consume()


@pytest.mark.asyncio
async def test_consume_empty_queue(config_path: str, backend: BaseBackend):
    c = load_settings(config_path)
    configure_logging(c)
    async with Jobs(c, backend) as j:
        def terminate():
            time.sleep(0.5)
            j._running = False

        thread = threading.Thread(target=terminate, daemon=True)
        thread.start()

        async with respx.mock:
            respx.get(
                "https://console.example.com/agent/jobs/queue/next",
                status_code=204,
            )
            await j.consume()


@pytest.mark.asyncio
async def test_do_not_process_failed_job_responses(capsys, config_path: str,
                                                   backend: BaseBackend):
    c = load_settings(config_path)

    configure_logging(c)
    async with Jobs(c, backend) as j:
        def terminate():
            time.sleep(0.5)
            j._running = False

        thread = threading.Thread(target=terminate, daemon=True)
        thread.start()

        async with respx.mock:
            respx.get(
                "https://console.example.com/agent/jobs/queue/next",
                status_code=400
            )
            await j.consume()

        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Failed to fetch jobs from ChaosIQ" in captured.err


@pytest.mark.asyncio
async def test_do_not_process_invalid_job_responses(capsys, config_path: str,
                                                    backend: BaseBackend):
    c = load_settings(config_path)

    configure_logging(c)
    async with Jobs(c, backend) as j:
        def terminate():
            time.sleep(0.5)
            j._running = False

        thread = threading.Thread(target=terminate, daemon=True)
        thread.start()

        async with respx.mock:
            respx.get(
                "https://console.example.com/agent/jobs/queue/next",
                content='{"m": "h"',
                headers={"Content-Type": "application/json"}
            )
            await j.consume()

        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Failed to decode ChaosIQ's response" in captured.err


@pytest.mark.asyncio
async def test_do_not_process_invalid_jobs(capsys, config_path: str,
                                           backend: BaseBackend):
    c = load_settings(config_path)

    configure_logging(c)
    async with Jobs(c, backend) as j:
        def terminate():
            time.sleep(0.5)
            j._running = False

        thread = threading.Thread(target=terminate, daemon=True)
        thread.start()

        async with respx.mock:
            respx.get(
                "https://console.example.com/agent/jobs/queue/next",
                content=json.dumps({"id": 12324}),  # should be a UUID4
                headers={"Content-Type": "application/json"}
            )
            await j.consume()

        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Failed to parse job" in captured.err
