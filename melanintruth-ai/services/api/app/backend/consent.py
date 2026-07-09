from __future__ import annotations

from .audit import AuditService
from .entities import ConsentPurpose, ConsentRecord, now
from .errors import AuthorizationError, NotFoundError
from .repository import InMemoryRepository


class ConsentService:
    def __init__(self, repo: InMemoryRepository, audit: AuditService):
        self.repo = repo
        self.audit = audit

    def grant(self, user_id: str, purpose: ConsentPurpose, version: str = "2026-07") -> ConsentRecord:
        user = self.repo.users[user_id]
        record = ConsentRecord(user_id=user.id, tenant_id=user.tenant_id, purpose=purpose, version=version, granted=True)
        self.repo.consent[record.id] = record
        self.audit.record("consent.granted", "consent", record.id, user.id, user.tenant_id, {"purpose": purpose.value, "version": version})
        return record

    def revoke(self, user_id: str, record_id: str) -> None:
        record = self.repo.consent.get(record_id)
        if not record or record.user_id != user_id:
            raise NotFoundError("consent record not found")
        record.granted = False
        record.revoked_at = now()
        self.audit.record("consent.revoked", "consent", record.id, user_id, record.tenant_id, {"purpose": record.purpose.value})

    def assert_granted(self, user_id: str, purpose: ConsentPurpose) -> None:
        user = self.repo.users[user_id]
        for record in self.repo.consent.values():
            if record.user_id == user.id and record.tenant_id == user.tenant_id and record.purpose == purpose and record.granted and record.revoked_at is None:
                return
        raise AuthorizationError(f"valid {purpose.value} consent is required")

    def export_model_improvement_records(self, user_id: str) -> list[str]:
        try:
            self.assert_granted(user_id, ConsentPurpose.MODEL_IMPROVEMENT)
        except AuthorizationError:
            return []
        return [image.id for image in self.repo.images.values() if image.user_id == user_id and image.deleted_at is None]
