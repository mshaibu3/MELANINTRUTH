from __future__ import annotations

from .audit import AuditService
from .entities import now
from .repository import InMemoryRepository


class PrivacyService:
    def __init__(self, repo: InMemoryRepository, audit: AuditService):
        self.repo = repo
        self.audit = audit

    def export_user_data(self, user_id: str) -> dict[str, object]:
        user = self.repo.users[user_id]
        data = {"user_profile": {"id": user.id, "email": user.email, "tenant_id": user.tenant_id}, "consent_records": [c.__dict__ for c in self.repo.consent.values() if c.user_id == user.id and c.tenant_id == user.tenant_id], "image_metadata": [{"id": i.id, "content_type": i.content_type, "size_bytes": i.size_bytes, "status": i.status} for i in self.repo.images.values() if i.user_id == user.id and i.tenant_id == user.tenant_id], "analysis_metadata": [j.result for j in self.repo.analysis_jobs.values() if j.user_id == user.id and j.tenant_id == user.tenant_id], "render_metadata": [{"id": r.id, "status": r.status.value, "confidence": r.confidence, "safety_report": r.safety_report} for r in self.repo.render_jobs.values() if r.user_id == user.id and r.tenant_id == user.tenant_id], "audit_summary": [{"event_type": e.event_type, "resource_type": e.resource_type, "created_at": e.created_at.isoformat()} for e in self.repo.audit_events if e.actor_user_id == user.id and e.tenant_id == user.tenant_id]}
        self.audit.record("privacy.export_created", "user", user.id, user.id, user.tenant_id, {})
        return data

    def delete_user_data(self, user_id: str) -> None:
        user = self.repo.users[user_id]
        user.deleted_at = now()
        for session in self.repo.sessions.values():
            if session.user_id == user.id:
                session.revoked_at = now()
        for consent in self.repo.consent.values():
            if consent.user_id == user.id:
                consent.granted = False
                consent.revoked_at = now()
        for image in self.repo.images.values():
            if image.user_id == user.id:
                image.deleted_at = now()
                image.status = "deleted"
        self.audit.record("privacy.deletion_completed", "user", user.id, user.id, user.tenant_id, {})
