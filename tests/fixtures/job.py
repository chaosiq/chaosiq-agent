import uuid
from typing import Literal

from chaosiqagent.types import Job


def create_job(target_type: Literal["experiment", "verification"] = None):
    target_id = uuid.uuid4()
    if not target_type:
        target_type = "experiment"
    return Job(
        id=uuid.uuid4(),
        agent_id=uuid.uuid4(),
        target_id=target_id,
        target_type=target_type,
        target_url=f"https://console.example.com/assets/{target_type}s/{target_id}",
        access_token="azerty1234",
        payload={},
    )
