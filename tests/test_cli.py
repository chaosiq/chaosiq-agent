# type: ignore

from multiprocessing import Process, Queue
import pytest
import tempfile
import time

from click.testing import CliRunner

from chaosiqagent.cli import cli

cfg = b"""
DEBUG=0
LOG_FORMAT="plain"
AGENT_URL=https://console.chaosiq.dev
AGENT_ACCESS_TOKEN=1234
"""

invalid_cfg = b"""
"""

pytestmark = pytest.mark.skip

def test_run_starts_application():
    def runit(queue: Queue):
        with tempfile.NamedTemporaryFile() as f:
            try:
                f.write(cfg)
                f.seek(0)
                runner = CliRunner()
                result = runner.invoke(cli, ['run', '--config', f.name])
                queue.put(result.exit_code)
            finally:
                pass

    q = Queue()
    p = Process(target=runit, args=(q, ))
    try:
        p.start()
        time.sleep(2)
    finally:
        p.terminate()
        p.join(1)

    exit_code = q.get()
    assert exit_code == 0


def test_run_fails_when_config_is_invalid():
    def runit(queue: Queue):
        with tempfile.NamedTemporaryFile() as f:
            try:
                f.write(invalid_cfg)
                f.seek(0)
                runner = CliRunner()
                result = runner.invoke(cli, ['run', '--config', f.name])
                queue.put(result.exit_code)
            finally:
                pass

    q = Queue()
    p = Process(target=runit, args=(q, ))
    try:
        p.start()
        time.sleep(2)
    finally:
        p.terminate()
        p.join(1)

    exit_code = q.get()
    assert exit_code == 1
