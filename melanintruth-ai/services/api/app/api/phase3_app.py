from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.backend.entities import ConsentPurpose, ModelVersion, RenderStatus
from app.backend.errors import AuthenticationError, AuthorizationError, ConflictError, DomainError, NotFoundError, ValidationError
from app.backend.vision import Image, sample_image
from app.core.errors import ApiError, structured_error
from app.db.repositories.sqlite import SQLiteRepository
from app.db.session import connect_sqlite
from app.schemas.common import SCIENTIFIC_LIMITATION
from app.services.wiring import build_container


class ApiApplication:
    """FastAPI-facing application service used by routes and dependency-light tests."""

    def __init__(self, repo: SQLiteRepository | None = None):
        self.repo = repo or SQLiteRepository(connect_sqlite())
        self.services = build_container(self.repo)
        self.tokens: dict[str, str] = {}
        self.refresh_sessions: dict[str, str] = {}
        self.privacy_exports: dict[str, dict[str, Any]] = {}
        self.privacy_deletions: dict[str, dict[str, Any]] = {}
        self.dataset_versions: list[dict[str, Any]] = []
        self.bias_report_records: list[dict[str, Any]] = []
        self.incidents: list[dict[str, Any]] = []

    def _persist_user_related(self, kind: str, record: Any, tenant_id: str | None, user_id: str | None) -> None:
        self.repo.persist_record(kind, record, tenant_id=tenant_id, user_id=user_id)

    def _issue(self, user_id: str, tokens: dict[str, str]) -> dict[str, str]:
        access = tokens["access_token"]
        self.tokens[access] = user_id
        self.refresh_sessions[tokens["refresh_token"]] = tokens["session_id"]
        return tokens

    def current_user(self, access_token: str | None):
        if not access_token or access_token not in self.tokens:
            raise ApiError("AUTH_REQUIRED", "Authentication is required.", 401)
        user = self.repo.users[self.tokens[access_token]]
        if user.deleted_at:
            raise ApiError("FORBIDDEN", "Account is deleted or disabled.", 403)
        return user

    def require_admin(self, access_token: str | None):
        user = self.current_user(access_token)
        if "admin" not in user.roles:
            raise ApiError("FORBIDDEN", "Admin role required.", 403)
        return user

    def register(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        try:
            user = self.services.auth.register(payload["email"], payload["password"], roles=set(payload.get("roles", ["user"])))
            self._persist_user_related("user", user, user.tenant_id, user.id)
            return 201, {"user_id": user.id, "tenant_id": user.tenant_id, "email": user.email}
        except ConflictError as exc:
            return 409, structured_error("VALIDATION_ERROR", str(exc))
        except DomainError as exc:
            return 422, structured_error("VALIDATION_ERROR", str(exc))

    def login(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        try:
            tokens = self.services.auth.login(payload["email"], payload["password"], payload.get("device_label", "unknown"))
            session = self.repo.sessions[tokens["session_id"]]
            self._persist_user_related("session", session, session.tenant_id, session.user_id)
            return 200, self._issue(session.user_id, tokens)
        except AuthenticationError as exc:
            return 401, structured_error("AUTH_REQUIRED", str(exc))

    def refresh(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        try:
            session_id = payload.get("session_id") or self.refresh_sessions.get(payload["refresh_token"])
            tokens = self.services.auth.refresh(session_id, payload["refresh_token"])
            self.refresh_sessions.pop(payload["refresh_token"], None)
            self._persist_user_related("session", self.repo.sessions[tokens["session_id"]], self.repo.sessions[tokens["session_id"]].tenant_id, self.repo.sessions[tokens["session_id"]].user_id)
            return 200, self._issue(self.repo.sessions[tokens["session_id"]].user_id, tokens)
        except (AuthenticationError, KeyError) as exc:
            return 401, structured_error("AUTH_REQUIRED", str(exc))

    def logout(self, access_token: str, session_id: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        self.services.auth.logout(user.id, session_id)
        self.repo.persist_record("session", self.repo.sessions[session_id], user.tenant_id, user.id)
        return 200, {"status": "logged_out"}

    def sessions(self, access_token: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        return 200, {"sessions": [{"id": s.id, "device_id": s.device_id, "revoked": s.revoked_at is not None} for s in self.repo.sessions.values() if s.user_id == user.id]}

    def account_deletion_request(self, access_token: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        self.services.auth.request_account_deletion(user.id)
        return 202, {"status": "requested"}

    def grant_consent(self, access_token: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        record = self.services.consent.grant(user.id, ConsentPurpose(payload["purpose"]), payload.get("version", "2026-07"))
        self._persist_user_related("consent", record, user.tenant_id, user.id)
        return 201, {"id": record.id, "purpose": record.purpose.value, "granted": record.granted, "version": record.version}

    def list_consent(self, access_token: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        return 200, {"consent": [{"id": c.id, "purpose": c.purpose.value, "granted": c.granted, "revoked": c.revoked_at is not None} for c in self.repo.consent.values() if c.user_id == user.id]}

    def revoke_consent(self, access_token: str, consent_id: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        self.services.consent.revoke(user.id, consent_id)
        self._persist_user_related("consent", self.repo.consent[consent_id], user.tenant_id, user.id)
        return 200, {"id": consent_id, "revoked": True}

    def upload_request(self, access_token: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        try:
            ticket = self.services.images.request_upload(user.id, payload["content_type"], payload["size_bytes"], payload["checksum_sha256"])
            return 201, {"upload_url": ticket.upload_url, "checksum_sha256": ticket.checksum_sha256}
        except AuthorizationError as exc:
            return 403, structured_error("CONSENT_REQUIRED", str(exc))
        except ValidationError as exc:
            return 422, structured_error("VALIDATION_ERROR", str(exc))

    def upload_complete(self, access_token: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        ticket = self.services.images.storage.signed_upload_url(user.tenant_id, payload["checksum_sha256"])
        try:
            image = self.services.images.complete_upload(user.id, ticket, payload["content_type"], payload["size_bytes"])
            self._persist_user_related("image", image, user.tenant_id, user.id)
            return 201, {"image_id": image.id, "status": image.status}
        except AuthorizationError as exc:
            return 403, structured_error("CONSENT_REQUIRED", str(exc))

    def get_image(self, access_token: str, image_id: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        try:
            return 200, self.services.images.public_metadata(user.id, image_id)
        except (AuthorizationError, NotFoundError) as exc:
            return 404, structured_error("IMAGE_NOT_FOUND", str(exc))

    def delete_image(self, access_token: str, image_id: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        self.services.images.delete(user.id, image_id)
        self._persist_user_related("image", self.repo.images[image_id], user.tenant_id, user.id)
        return 200, {"deleted": True}

    def create_analysis(self, access_token: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        try:
            user = self.current_user(access_token)
        except ApiError as exc:
            return exc.status_code, exc.response()
        pixels = sample_image(payload.get("sample_value", 128)) if "pixels" not in payload else payload["pixels"]
        try:
            job = self.services.analysis.create_job(user.id, payload["image_id"], pixels, cloud=payload.get("cloud", True))
            self._persist_user_related("analysis", job, user.tenant_id, user.id)
            return 201, self._analysis_response(job)
        except AuthorizationError as exc:
            msg = str(exc)
            code = "CONSENT_REQUIRED" if "consent" in msg else "TENANT_ACCESS_DENIED"
            return 403, structured_error(code, msg)

    def _analysis_response(self, job: Any) -> dict[str, Any]:
        return {
            "id": job.id,
            "status": job.status.value,
            "image_id": job.image_id,
            "model_version": job.model_version,
            "lighting_quality_score": job.lighting_score,
            "capture_quality_score": job.quality_score,
            "confidence_score": job.confidence,
            "uncertainty_score": job.uncertainty,
            "failure_reason": job.failure_reason,
            "result": job.result,
            "limitation_warning": SCIENTIFIC_LIMITATION,
            "retake_recommendation": job.result.get("retake_recommendation") if job.result else "Retake in even indirect lighting.",
        }

    def list_analysis(self, access_token: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        return 200, {"jobs": [self._analysis_response(job) for job in self.services.analysis.list_jobs(user.id)]}

    def get_analysis(self, access_token: str, job_id: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        try:
            return 200, self._analysis_response(self.services.analysis.get_job(user.id, job_id))
        except NotFoundError as exc:
            return 404, structured_error("ANALYSIS_NOT_FOUND", str(exc))

    def create_render(self, access_token: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        original: Image = payload.get("original") or [[(120 + ((x + y) % 2) * 10, 105, 95) for x in range(16)] for y in range(16)]
        rendered = payload.get("rendered")
        try:
            job = self.services.rendering.create_render(user.id, payload["analysis_id"], original, rendered=rendered, confidence=payload.get("confidence"))
            self._persist_user_related("render", job, user.tenant_id, user.id)
            status_code = 202 if job.status == RenderStatus.REJECTED_BY_SAFETY_GATE else 201
            return status_code, self._render_response(job)
                except ValidationError as exc:
            return 422, structured_error("ANALYSIS_NOT_COMPLETED", str(exc))
        except AuthorizationError as exc:
            msg = str(exc)
            if "analysis" in msg.lower() or "not found" in msg.lower() or "completed" in msg.lower():
                return 422, structured_error("ANALYSIS_NOT_COMPLETED", msg)
            return 403, structured_error("CONSENT_REQUIRED", msg)

    def _render_response(self, job: Any) -> dict[str, Any]:
        public_render_available = job.status == RenderStatus.COMPLETED
        return {
            "id": job.id,
            "status": job.status.value,
            "render_status": job.status.value,
            "analysis_id": job.analysis_id,
            "confidence_score": job.confidence,
            "uncertainty_score": job.uncertainty,
            "safety_gate_result": job.safety_report,
            "public_render_available": public_render_available,
            "rendered_image_reference": "derived/redacted" if public_render_available else None,
            "limitation_warning": SCIENTIFIC_LIMITATION,
        }

    def list_renders(self, access_token: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        return 200, {"renders": [self._render_response(r) for r in self.repo.render_jobs.values() if r.user_id == user.id]}

    def get_render(self, access_token: str, render_id: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        render = self.repo.render_jobs.get(render_id)
        if not render or render.user_id != user.id:
            return 404, structured_error("TENANT_ACCESS_DENIED", "Render not found for current tenant/user.")
        return 200, self._render_response(render)

    def privacy_export(self, access_token: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        data = self.services.privacy.export_user_data(user.id)
        request_id = f"export-{len(self.privacy_exports) + 1}"
        self.privacy_exports[request_id] = {"id": request_id, "status": "completed", "data": data, "tenant_id": user.tenant_id, "user_id": user.id}
        return 202, {"request_id": request_id, "status": "completed"}

    def get_privacy_export(self, access_token: str, request_id: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        export = self.privacy_exports[request_id]
        if export["user_id"] != user.id:
            return 404, structured_error("TENANT_ACCESS_DENIED", "Export not found.")
        return 200, export

    def privacy_delete(self, access_token: str) -> tuple[int, dict[str, Any]]:
        user = self.current_user(access_token)
        self.services.privacy.delete_user_data(user.id)
        request_id = f"delete-{len(self.privacy_deletions) + 1}"
        self.privacy_deletions[request_id] = {"id": request_id, "status": "completed", "tenant_id": user.tenant_id, "user_id": user.id}
        return 202, {"request_id": request_id, "status": "completed"}

    def governance_model_create(self, access_token: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        try:
            user = self.require_admin(access_token)
        except ApiError as exc:
            return exc.status_code, exc.response()
        try:
            approval_date = datetime.now(timezone.utc) if payload.get("approval_date") else None
            model = ModelVersion(approval_date=approval_date, **{k: v for k, v in payload.items() if k != "approval_date"})
            created = self.services.governance.create_model_version(user.id, model)
            self._persist_user_related("model_version", created, user.tenant_id, user.id)
            return 201, {"id": created.id, "model_id": created.model_id, "version": created.version, "status": created.status}
        except AuthorizationError as exc:
            return 403, structured_error("FORBIDDEN", str(exc))
        except ValidationError as exc:
            return 422, structured_error("GOVERNANCE_APPROVAL_REQUIRED", str(exc))

    def governance_model_list(self, access_token: str) -> tuple[int, dict[str, Any]]:
        self.current_user(access_token)
        return 200, {"model_versions": [{"id": m.id, "model_id": m.model_id, "version": m.version, "status": m.status} for m in self.repo.model_versions.values()]}

    def dataset_create(self, access_token: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        self.require_admin(access_token)
        if not payload.get("provenance_notes"):
            return 422, structured_error("VALIDATION_ERROR", "Dataset provenance notes are required.")
        record = {"id": f"dataset-{len(self.dataset_versions) + 1}", **payload}
        self.dataset_versions.append(record)
        return 201, record

    def dataset_list(self, access_token: str) -> tuple[int, dict[str, Any]]:
        self.current_user(access_token)
        return 200, {"dataset_versions": self.dataset_versions}

    def bias_reports(self, access_token: str) -> tuple[int, dict[str, Any]]:
        self.current_user(access_token)
        return 200, {"bias_reports": self.bias_report_records}

    def incident_create(self, access_token: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        self.require_admin(access_token)
        if not payload.get("severity") or not payload.get("mitigation_status"):
            return 422, structured_error("VALIDATION_ERROR", "Severity and mitigation status are required.")
        record = {"id": f"incident-{len(self.incidents) + 1}", **payload}
        self.incidents.append(record)
        return 201, record

    def audit(self, access_token: str) -> tuple[int, dict[str, Any]]:
        self.require_admin(access_token)
        return 200, {"audit": [event.__dict__ for event in self.repo.audit_events]}

    def openapi_contract(self) -> dict[str, Any]:
        paths = {
            path: {}
            for path in [
                "/health",
                "/auth/register",
                "/auth/login",
                "/auth/refresh",
                "/auth/logout",
                "/auth/sessions",
                "/auth/account-deletion-request",
                "/consent",
                "/images/upload-request",
                "/images/upload-complete",
                "/images/{image_id}",
                "/analysis/jobs",
                "/analysis/jobs/{job_id}",
                "/renders",
                "/renders/{render_id}",
                "/privacy/export",
                "/privacy/delete",
                "/governance/model-versions",
                "/governance/dataset-versions",
                "/governance/bias-reports",
                "/governance/incidents",
                "/governance/audit",
            ]
        }
        return {
            "openapi": "3.1.0",
            "info": {"title": "MelaninTruth AI API", "version": "0.3.7"},
            "paths": paths,
            "components": {
                "securitySchemes": {"BearerAuth": {"type": "http", "scheme": "bearer"}},
                "schemas": {
                    "ErrorEnvelope": {
                        "type": "object",
                        "required": ["error"],
                        "properties": {"error": {"$ref": "#/components/schemas/ErrorDetail"}},
                    },
                    "ErrorDetail": {
                        "type": "object",
                        "required": ["code", "message", "details"],
                        "properties": {
                            "code": {"type": "string"},
                            "message": {"type": "string"},
                            "details": {"type": "object"},
                        },
                    },
                    "AnalysisJobResponse": {
                        "type": "object",
                        "required": [
                            "confidence_score",
                            "uncertainty_score",
                            "lighting_quality_score",
                            "capture_quality_score",
                            "limitation_warning",
                        ],
                    },
                    "RenderResponse": {
                        "type": "object",
                        "required": [
                            "confidence_score",
                            "uncertainty_score",
                            "safety_gate_result",
                            "render_status",
                            "public_render_available",
                            "limitation_warning",
                        ],
                    },
                },
            },
        }
