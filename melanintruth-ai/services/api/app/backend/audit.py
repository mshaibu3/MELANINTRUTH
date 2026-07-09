from __future__ import annotations

import hashlib
from typing import Any

from .entities import AuditEvent
from .repository import InMemoryRepository

SENSITIVE_KEYS = {"password", "token", "access_token", "refresh_token", "raw_image", "raw_storage_path", "storage_path", "biometric_template", "storage_ref"}


def _clean(metadata: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in metadata.items() if key.lower() not in SENSITIVE_KEYS and "token" not in key.lower() and "raw" not in key.lower()}


def hash_context(value: str | None) -> str:
    if not value:
        return "context-not-captured"
    return hashlib.sha256(value.encode()).hexdigest()


class AuditService:
    def __init__(self, repo: InMemoryRepository):
        self.repo = repo

    def record(self, event_type: str, resource_type: str, resource_id: str | None, actor_user_id: str | None, tenant_id: str | None, metadata: dict[str, Any] | None = None, ip: str | None = None, user_agent: str | None = None) -> AuditEvent:
        event = AuditEvent(actor_user_id=actor_user_id, tenant_id=tenant_id, event_type=event_type, resource_type=resource_type, resource_id=resource_id, metadata=_clean(metadata or {}), ip_hash=hash_context(ip), user_agent_hash=hash_context(user_agent))
        self.repo.audit_events.append(event)
        return event
