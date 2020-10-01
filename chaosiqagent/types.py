import asyncio
from datetime import datetime
from typing import Literal, Optional, Dict, Any, List

from pydantic import BaseModel, BaseSettings, Field, UUID4, AnyUrl, PositiveInt
from pydantic.fields import Undefined

__all__ = ["Config", "Job", "Backend", "Futures"]


Backend = Literal["null", "kubernetes", "shell"]
Futures = List[asyncio.Future]


class Config(BaseSettings):
    debug: bool = False
    log_format: Literal["plain", "structured"]
    agent_url: AnyUrl = Field(..., env='AGENT_URL')
    agent_access_token: str = Field(..., env='AGENT_ACCESS_TOKEN')
    agent_backend: Backend = Field(
        "null", env='AGENT_BACKEND')
    verify_tls: bool = Field(True, env='VERIFY_TLS')
    # This binary is used for shell backend
    chaos_binary: str = Field(Undefined, env='CHAOS_BINARY')
    heartbeat_interval: PositiveInt = Field(900, env='HEARTBEAT_INTERVAL')
    # Default docker image containing the Chaos Toolkit (K8s)
    ctk_docker_image: str = Field(
        'chaosiq/chaostoolkit', env='CTK_DOCKER_IMAGE')


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
