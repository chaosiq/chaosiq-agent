from ..types import Config
from .base import BaseBackend, NullBackend

__all__ = ["get_backend"]


def get_backend(config: Config) -> BaseBackend:
    """
    Instanciate the backend from the configuration `BACKEND` key.

    If none is provided, defaults to the `NullBackend`.
    """
    backend_name = config.agent_backend
    if backend_name == "kubernetes":
        from .k8s import K8SBackend
        return K8SBackend(config)
    elif backend_name == "shell":
        from .shell import ShellBackend
        return ShellBackend(config)
    elif backend_name == "null":
        return NullBackend(config)
