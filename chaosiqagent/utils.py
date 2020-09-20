from .log import logger
from .types import Futures

__all__ = ["raise_if_errored"]


def raise_if_errored(done: Futures, pending: Futures) -> None:
    """
    Take a list of futues
    """
    if len(pending) > 0:
        logger.debug(f"{len(pending)} tasks are still pending")

    for t in done:
        if t.cancelled():
            logger.warning(f"Task {str(t)} was cancelled")
            continue

        x = t.exception()
        if x:
            logger.error(f"Failed to setup properly: {str(x)}")
            raise x
