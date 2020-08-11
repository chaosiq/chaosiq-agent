import decimal
import logging
import logging.config
import uuid
from datetime import date, datetime
from typing import Any

from pythonjsonlogger import jsonlogger
import simplejson

from .types import Config

__all__ = ["configure_logging", "logger"]
logger = logging.getLogger("chaosiqagent")


def encoder(o: Any) -> str:  # pragma: no cover
    """
    Perform some additional encoding for types JSON doesn't support natively.
    We don't try to respect any ECMA specification here as we want to retain
    as much information as we can.
    """
    if isinstance(o, (date, datetime)):
        # we do not meddle with the timezone and assume the date was stored
        # with the right information of timezone as +-HH:MM
        return o.isoformat()
    elif isinstance(o, decimal.Decimal):
        return str(o)
    elif isinstance(o, uuid.UUID):
        return str(o)

    raise TypeError(
        "Object of type '{}' is not JSON serializable".format(type(o)))


def configure_logging(config: Config) -> None:
    """
    Configure the application's logger.

    Look into the configuration for two options:

    * DEBUG: to enable `"DEBUG"` level, `"INFO"` otherwise
    * LOG_FORMAT: to define which format should be used to log `"plain"` or
      `"structured"` for json logging
    """
    verbose = config.debug
    log_format = config.log_format
    level = logging.DEBUG if verbose else logging.INFO

    struct_fmt = "%(process) %(asctime) %(levelname) %(module) %(lineno) " \
                 "%(message) %(trace)"
    cfg = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
            },
            "structured": {
                "()": jsonlogger.JsonFormatter,
                "fmt": struct_fmt,
                "json_default": encoder,
                "json_serializer": simplejson.dumps,
                "json_indent": None,
                "timestamp": True
            }
        },
        "handlers": {
            "default": {
                "level": level,
                "class": "logging.StreamHandler",
                "formatter": log_format,
            }
        },
        "loggers": {
            "chaosiqagent": {
                "handlers": ["default"],
                "level": level,
                "propagate": False
            }
        }
    }

    logging.config.dictConfig(cfg)
