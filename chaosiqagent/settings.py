# -*- coding: utf-8 -*-
from .types import Config

__all__ = ["load_settings"]


def load_settings(env_path: str) -> Config:
    """
    Load settings from the dot env file.
    """
    return Config(_env_file=env_path, _env_file_encoding="utf-8")
