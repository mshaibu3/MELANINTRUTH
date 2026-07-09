from __future__ import annotations

from .audit import AuditService
from .consent import ConsentService
from .entities import ConsentPurpose, JobStatus, RenderJob, RenderStatus, now
from .errors import ValidationError
from .repository import InMemoryRepository
from .vision import LIMITATION_WARNING, Image, SafetyGate


class RenderService:
    def __init__(self, repo: InMemoryRepository, audit: AuditService, consent: ConsentService, safety_gate: SafetyGate | None = None):
        self.repo = repo
        self.audit = audit
        self.consent = consent
        self.safety_gate = safety_gate or SafetyGate()

    def create_render(self, user_id: str, analysis_id: str, original: Image, rendered: Image | None = None, confidence: float | None = None) -> RenderJob:
        self.consent.assert_granted(user_id, ConsentPurpose.IMAGE_PROCESSING)
        analysis = self.repo.analysis_jobs.get(analysis_id)
        if not analysis or analysis.user_id != user_id or analysis.status != JobStatus.COMPLETED:
            raise ValidationError("completed source analysis is required before rendering")
        user = self.repo.users[user_id]
        job = RenderJob(user_id=user.id, tenant_id=user.tenant_id, analysis_id=analysis_id)
        self.repo.render_jobs[job.id] = job
        job.status = RenderStatus.RENDERING
        output = rendered or [row[:] for row in original]
        job.confidence = analysis.confidence if confidence is None else confidence
        job.uncertainty = 1 - job.confidence
        report = self.safety_gate.evaluate(original, output, job.confidence)
        job.safety_report = report
        if not report["passed"]:
            job.status = RenderStatus.REJECTED_BY_SAFETY_GATE
            self.audit.record("render.rejected_by_safety_gate", "render_job", job.id, user.id, user.tenant_id, {"failed_checks": report["failed_checks"], "risk_level": report["risk_level"]})
            return job
        job.status = RenderStatus.COMPLETED
        job.rendered_ref = f"derived://tenant/{user.tenant_id}/render/{job.id}"
        job.updated_at = now()
        self.audit.record("render.completed", "render_job", job.id, user.id, user.tenant_id, {"confidence": job.confidence})
        return job

    def public_result(self, user_id: str, render_id: str) -> dict[str, object]:
        job = self.repo.render_jobs[render_id]
        if job.user_id != user_id or job.status != RenderStatus.COMPLETED:
            raise ValidationError("render is not available as a valid result")
        return {"render_id": job.id, "status": job.status.value, "rendered_image_reference": "derived/redacted", "confidence_score": job.confidence, "uncertainty_score": job.uncertainty, "safety_report": job.safety_report, "explanation": LIMITATION_WARNING, "limitation_warning": LIMITATION_WARNING}
