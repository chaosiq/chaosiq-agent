# type: ignore
import json
import logging
from tempfile import NamedTemporaryFile

from chaosiqagent.log import configure_logging
from chaosiqagent.settings import load_settings


def test_can_log_as_plaintext_to_stderr(capsys, config_path: str):
    configure_logging(load_settings(config_path))

    logger = logging.getLogger("chaosiqagent")
    logger.info("hello")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "INFO chaosiqagent hello" in captured.err


def test_can_log_structured_to_stderr(capsys, config_path: str):
    with open(config_path) as d:
        with NamedTemporaryFile() as f:
            r = d.read()
            r = r.replace("plain", "structured")
            f.write(r.encode('utf-8'))
            f.seek(0)
            configure_logging(load_settings(f.name))

    logger = logging.getLogger("chaosiqagent")
    logger.info("hello")

    captured = capsys.readouterr()
    assert captured.out == ""

    event = json.loads(captured.err)
    assert event["message"] == "hello"
    assert event["levelname"] == "INFO"


def test_must_not_log_debug_messages_when_not_verbose(capsys, config_path: str):
    with open(config_path) as d:
        with NamedTemporaryFile() as f:
            r = d.read()
            r = r.replace("1", "0")
            f.write(r.encode('utf-8'))
            f.seek(0)
            configure_logging(load_settings(f.name))

    logger = logging.getLogger("chaosiqagent")
    logger.debug("hello")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
