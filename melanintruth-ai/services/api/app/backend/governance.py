from __future__ import annotations

from .audit import AuditService
from .entities import ModelVersion
from .errors import AuthorizationError, ValidationError
from .repository import InMemoryRepository


class GovernanceService:
    def __init__(self, repo: InMemoryRepository, audit: AuditService):
        self.repo = repo
        self.audit = audit

    def create_model_version(self, actor_user_id: str, model: ModelVersion) -> ModelVersion:
        actor = self.repo.users[actor_user_id]
        if "admin" not in actor.roles:
            raise AuthorizationError("admin role required")
        if not model.known_limitations or len(model.known_limitations) < 10:
            raise ValidationError("model version requires meaningful limitation text")
        if model.status == "production" and (not model.approved_by or not model.approval_date):
            raise ValidationError("production model requires approval fields")
        self.repo.model_versions[model.id] = model
        self.audit.record("governance.model_version_created", "model_version", model.id, actor.id, actor.tenant_id, {"model_id": model.model_id, "version": model.version, "status": model.status})
        return model
