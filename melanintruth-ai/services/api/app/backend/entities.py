from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def now() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class ConsentPurpose(str, Enum):
    IMAGE_PROCESSING = "image_processing"
    CLOUD_PROCESSING = "cloud_processing"
    LOCAL_PROCESSING = "local_processing"
    DATA_RETENTION = "data_retention"
    MODEL_IMPROVEMENT = "model_improvement"
    ENTERPRISE_SHARING = "enterprise_sharing"
    MARKETING = "marketing"
    ANALYTICS = "analytics"


class JobStatus(str, Enum):
    PENDING = "pending"
    QUALITY_CHECKED = "quality_checked"
    REJECTED_LOW_QUALITY = "rejected_low_quality"
    ANALYSING = "analysing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


class RenderStatus(str, Enum):
    PENDING = "pending"
    RENDERING = "rendering"
    REJECTED_BY_SAFETY_GATE = "rejected_by_safety_gate"
    COMPLETED = "completed"
    FAILED = "failed"
    DELETED = "deleted"


@dataclass
class User:
    email: str
    password_hash: str
    tenant_id: str
    id: str = field(default_factory=new_id)
    roles: set[str] = field(default_factory=lambda: {"user"})
    deleted_at: datetime | None = None


@dataclass
class Device:
    user_id: str
    tenant_id: str
    label: str
    id: str = field(default_factory=new_id)
    revoked_at: datetime | None = None


@dataclass
class Session:
    user_id: str
    tenant_id: str
    device_id: str
    refresh_token_hash: str
    id: str = field(default_factory=new_id)
    revoked_at: datetime | None = None


@dataclass
class ConsentRecord:
    user_id: str
    tenant_id: str
    purpose: ConsentPurpose
    version: str
    granted: bool
    id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=now)
    revoked_at: datetime | None = None


@dataclass
class ImageCapture:
    user_id: str
    tenant_id: str
    checksum_sha256: str
    content_type: str
    size_bytes: int
    storage_ref: str
    id: str = field(default_factory=new_id)
    status: str = "available"
    deleted_at: datetime | None = None


@dataclass
class AnalysisJob:
    user_id: str
    tenant_id: str
    image_id: str
    id: str = field(default_factory=new_id)
    status: JobStatus = JobStatus.PENDING
    model_version: str = "baseline-visible-skin-v1"
    quality_score: float = 0.0
    lighting_score: float = 0.0
    confidence: float = 0.0
    uncertainty: float = 1.0
    failure_reason: str | None = None
    result: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)


@dataclass
class RenderJob:
    user_id: str
    tenant_id: str
    analysis_id: str
    id: str = field(default_factory=new_id)
    status: RenderStatus = RenderStatus.PENDING
    confidence: float = 0.0
    uncertainty: float = 1.0
    safety_report: dict[str, Any] = field(default_factory=dict)
    rendered_ref: str | None = None
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)


@dataclass
class AuditEvent:
    actor_user_id: str | None
    tenant_id: str | None
    event_type: str
    resource_type: str
    resource_id: str | None
    metadata: dict[str, Any]
    ip_hash: str = "context-not-captured"
    user_agent_hash: str = "context-not-captured"
    event_id: str = field(default_factory=new_id)
    created_at: datetime = field(default_factory=now)


@dataclass
class ModelVersion:
    model_id: str
    version: str
    purpose: str
    status: str
    known_limitations: str
    supported_skin_tone_ranges: list[str]
    supported_lighting_conditions: list[str]
    prohibited_uses: list[str]
    approved_by: str | None = None
    approval_date: datetime | None = None
    evaluation_summary: str = ""
    id: str = field(default_factory=new_id)
