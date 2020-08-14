from datetime import datetime
from typing import Literal, Optional, Dict, Any

from pydantic import BaseModel, BaseSettings, Field, UUID4, AnyUrl
from pydantic.fields import Undefined

__all__ = ["Config", "Job", "Backend"]


Backend = Literal["null", "kubernetes", "shell"]


class Config(BaseSettings):
    debug: bool = False
    log_format: Literal["plain", "structured"]
    agent_url: AnyUrl = Field(..., env='AGENT_URL')
    agent_access_token: str = Field(..., env='AGENT_ACCESS_TOKEN')
    agent_backend: Backend = Field(
        "null", env='AGENT_BACKEND')
    verify_tls: bool = Field(False, env='VERIFY_TLS')
    chaos_binary: str = Field(Undefined, env='CHAOS_BINARY')


class Job(BaseModel):
    id: UUID4
    agent_id: UUID4
    org_id: UUID4
    team_id: Optional[UUID4]

    target_id: UUID4
    target_type: Literal["experiment", "verification"]
    target_url: AnyUrl
    access_token: Optional[str]

    payload: Optional[Dict[str, Any]]
    run_at: Optional[datetime]
