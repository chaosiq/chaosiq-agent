# type: ignore
from tempfile import NamedTemporaryFile

from pydantic import ValidationError
import pytest

from chaosiqagent.settings import load_settings


def test_load_settings_from_dotenv_file(config_path: str):
    c = load_settings(config_path)
    assert c.debug is True


def test_cannot_load_test_in_non_utf8_encoding(config_path: str):
    with open(config_path, encoding='utf-8') as p:
        with NamedTemporaryFile() as f:
            f.write(p.read().encode('utf-16'))
            f.seek(0)

            with pytest.raises(UnicodeDecodeError):
                load_settings(f.name)


def test_cannot_load_settings_with_invalid_backend(config_path: str):
    with open(config_path, 'r') as p:
        with NamedTemporaryFile('w') as f:
            f.write(p.read())
            f.write('AGENT_BACKEND="invalid"')
            f.seek(0)

            with pytest.raises(ValidationError):
                load_settings(f.name)
