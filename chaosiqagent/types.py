from datetime import datetime
from typing import Literal, Optional, Dict, Any

from pydantic import BaseModel, BaseSettings, Field, UUID4, AnyUrl

__all__ = ["Config", "Job", "Backend"]


Backend = Literal["null", "kubernetes"]


class Config(BaseSettings):
    debug: bool = False
    log_format: Literal["plain", "structured"]
    agent_url: AnyUrl = Field(..., env='AGENT_URL')
    agent_access_token: str = Field(..., env='AGENT_ACCESS_TOKEN')
    agent_backend: Backend = Field(
        "null", env='AGENT_BACKEND')
    verify_tls: bool = Field(False, env='VERIFY_TLS')


class Job(BaseModel):
    id: UUID4
    agent_id: UUID4

    target_id: UUID4
    target_type: Literal["experiment", "verification"]
    target_url: AnyUrl
    access_token: Optional[bytes]

    payload: Optional[Dict[str, Any]]
    run_at: Optional[datetime]
