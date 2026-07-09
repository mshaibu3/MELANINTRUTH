from __future__ import annotations

from .audit import AuditService
from .consent import ConsentService
from .entities import AnalysisJob, ConsentPurpose, JobStatus, now
from .errors import NotFoundError
from .image_service import ImageService
from .repository import InMemoryRepository
from .vision import LIMITATION_WARNING, Image, brightness, image_quality


class AnalysisService:
    def __init__(self, repo: InMemoryRepository, audit: AuditService, consent: ConsentService, images: ImageService):
        self.repo = repo
        self.audit = audit
        self.consent = consent
        self.images = images

    def create_job(self, user_id: str, image_id: str, image_pixels: Image, cloud: bool = True) -> AnalysisJob:
        self.images.assert_available(user_id, image_id)
        self.consent.assert_granted(user_id, ConsentPurpose.IMAGE_PROCESSING)
        if cloud:
            self.consent.assert_granted(user_id, ConsentPurpose.CLOUD_PROCESSING)
        user = self.repo.users[user_id]
        job = AnalysisJob(user_id=user.id, tenant_id=user.tenant_id, image_id=image_id)
        self.repo.analysis_jobs[job.id] = job
        self.audit.record("analysis.job_created", "analysis_job", job.id, user.id, user.tenant_id, {"image_id": image_id})
        quality = image_quality(image_pixels)
        job.quality_score = float(quality["quality_score"])
        job.status = JobStatus.QUALITY_CHECKED
        if not quality["suitable_for_analysis"]:
            job.status = JobStatus.REJECTED_LOW_QUALITY
            job.failure_reason = ",".join(quality["failure_reasons"]) or "low_quality"
            job.confidence = job.quality_score
            job.uncertainty = 1 - job.confidence
            self.audit.record("analysis.rejected_low_quality", "analysis_job", job.id, user.id, user.tenant_id, {"failure_reason": job.failure_reason})
            return job
        job.status = JobStatus.ANALYSING
        lighting_score = max(0.0, min(1.0, 1 - abs(brightness(image_pixels) - 0.55)))
        job.lighting_score = lighting_score
        job.confidence = min(job.quality_score, lighting_score)
        job.uncertainty = 1 - job.confidence
        job.result = {"estimated_visible_skin_tone": "estimated visible tone under standardised lighting assumptions", "undertone_estimate": "neutral baseline", "pigmentation_distribution": "baseline metadata only", "lighting_quality_score": lighting_score, "capture_quality_score": job.quality_score, "confidence_score": job.confidence, "uncertainty_score": job.uncertainty, "explanation": LIMITATION_WARNING, "limitation_warning": LIMITATION_WARNING, "retake_recommendation": None if job.confidence >= 0.65 else "Retake in even indirect lighting for higher confidence."}
        job.status = JobStatus.COMPLETED
        job.updated_at = now()
        self.audit.record("analysis.completed", "analysis_job", job.id, user.id, user.tenant_id, {"model_version": job.model_version, "confidence": job.confidence})
        return job

    def get_job(self, user_id: str, job_id: str) -> AnalysisJob:
        job = self.repo.analysis_jobs.get(job_id)
        if not job or job.user_id != user_id:
            raise NotFoundError("analysis job not found")
        return job

    def list_jobs(self, user_id: str) -> list[AnalysisJob]:
        return [job for job in self.repo.analysis_jobs.values() if job.user_id == user_id and job.status != JobStatus.DELETED]
