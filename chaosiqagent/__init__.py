from importlib.metadata import version, PackageNotFoundError

__all__ = ["__version__"]


try:
    __version__ = version(__name__)
except PackageNotFoundError:
    __version__ = 'unknown'
