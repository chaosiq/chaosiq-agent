import pytest
from tempfile import NamedTemporaryFile

from chaosiqagent.backend import get_backend
from chaosiqagent.backend.base import BaseBackend, NullBackend
from chaosiqagent.log import configure_logging
from chaosiqagent.settings import load_settings
from chaosiqagent.types import Config


@pytest.mark.asyncio
async def test_null_backend_does_nothing_but_logging_jobs(capsys,
                                                          config_path: str):
    c = load_settings(config_path)
    configure_logging(c)

    j = {"stuff": "here"}

    b = NullBackend(c)
    await b.setup()
    await b.process_job(j)
    await b.cleanup()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"Backend 'null' got job: {j}" in captured.err


@pytest.mark.asyncio
async def test_cannot_implement_base_backend():
    b = BaseBackend({})

    with pytest.raises(NotImplementedError):
        await b.setup()

    with pytest.raises(NotImplementedError):
        await b.cleanup()

    with pytest.raises(NotImplementedError):
        await b.process_job({})


@pytest.mark.parametrize("name", ["null", "kubernetes", "shell"])
def test_get_backend(config_path: str, name):
    with open(config_path, 'r') as p:
        with NamedTemporaryFile('w') as f:
            f.write(p.read())
            f.write(f"AGENT_BACKEND=\"{name}\"")
            f.seek(0)

            config = load_settings(f.name)
            backend = get_backend(config)
            assert backend is not None
            assert isinstance(backend, BaseBackend)
