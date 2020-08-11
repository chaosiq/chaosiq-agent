# type: ignore
import os.path

import better_exceptions
import httpx
import pytest

from chaosiqagent.backend.base import BaseBackend
from chaosiqagent.settings import load_settings
from chaosiqagent.types import Config

cur_dir = os.path.abspath(os.path.dirname(__file__))
fixtures_dir = os.path.join(cur_dir, "fixtures")
better_exceptions.hook()


@pytest.fixture(scope="session", autouse=True)
def config_path() -> str:
    return os.path.abspath(os.path.join(fixtures_dir, '.env.test'))


@pytest.fixture(scope="session", autouse=True)
def config(config_path: str) -> Config:
    return load_settings(config_path)


@pytest.fixture
def backend(config: Config) -> BaseBackend:
    from fixtures.backend import DummyBackend
    return DummyBackend({})


@pytest.fixture
def http_test_client() -> httpx.AsyncClient:
    from fixtures.httpx_client import TestClient
    return TestClient()
 