from typing import Literal

from pydantic import BaseModel, BaseSettings, Field, UUID4, AnyUrl

__all__ = ["Config", "Job"]


class Config(BaseSettings):
    debug: bool = False
    log_format: Literal["plain", "structured"]
    agent_url: AnyUrl = Field(..., env='AGENT_URL')
    agent_access_token: str = Field(..., env='AGENT_ACCESS_TOKEN')
    agent_backend: Literal["null", "kubernetes"] = Field(
        "null", env='AGENT_BACKEND')


class Job(BaseModel):
    id: UUID4
