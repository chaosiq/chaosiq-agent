# type: ignore
import pytest
import yaml

from chaosiqagent.ctk import get_chaostoolkit_settings


def test_get_ctk_settings(config):

    settings = get_chaostoolkit_settings(config=config, token="azerty1234")
    assert settings not in [None, '']

    # ensure yaml is valid
    try:
        yaml.safe_load(settings)
    except yaml.YAMLError as exc:
        pytest.fail("settings YAML is not valid")

    # ensure all fields have been replaced
    assert '{' not in settings
    assert '}' not in settings
