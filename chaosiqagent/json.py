from typing import Any

from pydantic.json import pydantic_encoder
from simplejson import JSONEncoder as _JSONEncoder

__all__ = ["JSONEncoder"]


class JSONEncoder(_JSONEncoder):
    def default(self, obj: object) -> Any:
        return pydantic_encoder(obj)
