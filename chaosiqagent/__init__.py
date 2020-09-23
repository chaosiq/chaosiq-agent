from importlib.metadata import version, PackageNotFoundError

__all__ = ["__version__"]


try:
    __version__ = version("chaosiq-agent")
except PackageNotFoundError:  # pragma: no cover
    __version__ = 'unknown'
