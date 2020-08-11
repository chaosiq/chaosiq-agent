from enum import Enum

from pydantic import BaseModel, BaseSettings, Field, UUID4, AnyUrl

__all__ = ["Config", "Job"]


class LogFormatEnum(str, Enum):
    plain = "plain"
    structured = "structured"


class AgentBackendEnum(str, Enum):
    null = "null"
    kubernetes = "kubernetes"


class Config(BaseSettings):
    debug: bool = False
    log_format: LogFormatEnum = LogFormatEnum.plain
    agent_url: AnyUrl = Field(..., env='AGENT_URL')
    agent_access_token: str = Field(..., env='AGENT_ACCESS_TOKEN')
    agent_backend: AgentBackendEnum = Field(
        AgentBackendEnum.null, env='AGENT_BACKEND')


class Job(BaseModel):
    id: UUID4
