from typing import Any
from app.schemas.common import BaseModel, Field
if BaseModel is object:
    class AuditEventResponse(dict):
        pass
else:
    class AuditEventResponse(BaseModel):
        event_type: str
        resource_type: str
        metadata: dict[str, Any] = Field(default_factory=dict)
