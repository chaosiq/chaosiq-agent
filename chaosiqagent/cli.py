import asyncio

import click
from pydantic import ValidationError
import uvloop

from . import __version__
from .agent import Agent
from .log import configure_logging
from .settings import load_settings


@click.group()
@click.version_option(version=__version__)
def cli() -> None:  # pragma: no cover
    pass


@cli.command()
@click.option('--config', help='Configuration .env file.')
def run(config: str = None) -> None:  # pragma: no cover
    """
    Runs the application.
    """
    try:
        settings = load_settings(config)
    except ValidationError as e:
        raise click.ClickException(str(e))

    configure_logging(settings)
    uvloop.install()
    asyncio.run(Agent(settings).run())
