from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.backend.entities import AnalysisJob, AuditEvent, ConsentPurpose, ConsentRecord, ImageCapture, JobStatus, ModelVersion, RenderJob, RenderStatus, Session, User
from app.backend.repository import InMemoryRepository

try:
    from sqlmodel import Session as SQLSession, select
    from app.db import models as m
except ModuleNotFoundError:
    SQLSession = None  # type: ignore[assignment]


class _PersistingAuditList(list[AuditEvent]):
    def __init__(self, repo: "SQLModelRepository"):
        super().__init__()
        self.repo = repo

    def append(self, event: AuditEvent) -> None:  # type: ignore[override]
        super().append(event)
        self.repo._persist_audit_event(event)


class SQLModelRepository(InMemoryRepository):
    """Concrete SQLModel runtime repository while retaining Phase 2 service maps.

    Phase 2 services use in-memory maps for deterministic unit tests. This repository mirrors
    service writes to SQLModel tables when dependencies and a DB session are available, while the
    public API continues to redact tokens and internal storage references at the service boundary.
    """

    def __init__(self, session: Any):
        super().__init__()
        self.session = session
        self.audit_events = _PersistingAuditList(self)
        self.generic_records: list[dict[str, Any]] = []

    def _sql_enabled(self) -> bool:
        return SQLSession is not None and self.session is not None

    def persist_record(self, kind: str, record: Any, tenant_id: str | None = None, user_id: str | None = None) -> None:
        dispatch = {
            "user": self.save_user,
            "session": self.save_session,
            "consent": self.save_consent,
            "image": self.save_image,
            "analysis": self.save_analysis,
            "render": self.save_render,
            "privacy_export": self.save_privacy_export,
            "privacy_deletion": self.save_privacy_deletion,
            "dataset_version": lambda item: self.save_dataset_version(item, tenant_id),
            "bias_report": lambda item: self.save_bias_report(item, tenant_id),
            "incident": lambda item: self.save_incident(item, tenant_id),
            "model_version": lambda item: self.save_model_version(item, tenant_id),
        }
        handler = dispatch.get(kind)
        if handler is not None:
            handler(record)
            return
        self.generic_records.append({"kind": kind, "tenant_id": tenant_id, "user_id": user_id, "record": record})

    def list_records(self, kind: str, tenant_id: str | None = None, user_id: str | None = None) -> list[dict[str, Any]]:
        return [
            item
            for item in self.generic_records
            if item["kind"] == kind
            and (tenant_id is None or item["tenant_id"] == tenant_id)
            and (user_id is None or item["user_id"] == user_id)
        ]

    def save_user(self, user: User) -> None:
        self.users[user.id] = user
        self.users_by_email[user.email] = user.id
        if self._sql_enabled():
            self.session.merge(m.UserORM(id=user.id, tenant_id=user.tenant_id, email=user.email, password_hash=user.password_hash, roles_json=sorted(user.roles), deleted_at=user.deleted_at))
            self.session.commit()

    def save_session(self, record: Session) -> None:
        self.sessions[record.id] = record
        if self._sql_enabled():
            self.session.merge(m.SessionORM(id=record.id, tenant_id=record.tenant_id, user_id=record.user_id, device_id=record.device_id, refresh_token_hash=record.refresh_token_hash, revoked_at=record.revoked_at))
            self.session.commit()

    def save_consent(self, record: ConsentRecord) -> None:
        self.consent[record.id] = record
        if self._sql_enabled():
            self.session.merge(m.ConsentRecordORM(id=record.id, tenant_id=record.tenant_id, user_id=record.user_id, purpose=record.purpose.value, version=record.version, granted=record.granted, revoked_at=record.revoked_at))
            self.session.commit()

    def save_image(self, record: ImageCapture) -> None:
        self.images[record.id] = record
        if self._sql_enabled():
            self.session.merge(m.ImageCaptureORM(id=record.id, tenant_id=record.tenant_id, user_id=record.user_id, checksum_sha256=record.checksum_sha256, content_type=record.content_type, size_bytes=record.size_bytes, storage_ref_encrypted=record.storage_ref, status=record.status, deleted_at=record.deleted_at))
            self.session.commit()

    def save_analysis(self, record: AnalysisJob) -> None:
        self.analysis_jobs[record.id] = record
        if self._sql_enabled():
            self.session.merge(m.AnalysisJobORM(id=record.id, tenant_id=record.tenant_id, user_id=record.user_id, image_id=record.image_id, status=record.status.value, model_version=record.model_version, quality_score=record.quality_score, lighting_score=record.lighting_score, confidence=record.confidence, uncertainty=record.uncertainty, failure_reason=record.failure_reason, result_json=record.result))
            self.session.commit()

    def save_render(self, record: RenderJob) -> None:
        self.render_jobs[record.id] = record
        if self._sql_enabled():
            self.session.merge(m.AuthenticRenderORM(id=record.id, tenant_id=record.tenant_id, user_id=record.user_id, analysis_id=record.analysis_id, status=record.status.value, confidence=record.confidence, uncertainty=record.uncertainty, rendered_ref_encrypted=record.rendered_ref, metadata_json={"safety_report_id": record.id}))
            self.session.merge(m.RenderSafetyReportORM(tenant_id=record.tenant_id, user_id=record.user_id, render_id=record.id, passed=bool(record.safety_report.get("passed")), risk_level=str(record.safety_report.get("risk_level", "unknown")), report_json=record.safety_report))
            self.session.commit()

    def _persist_audit_event(self, record: AuditEvent) -> None:
        if self._sql_enabled():
            self.session.merge(m.AuditLogORM(id=record.event_id, tenant_id=record.tenant_id, user_id=record.actor_user_id, event_type=record.event_type, resource_type=record.resource_type, resource_id=record.resource_id, metadata_json=record.metadata))
            self.session.commit()

    def save_audit(self, record: AuditEvent) -> None:
        self.audit_events.append(record)

    def save_model_version(self, record: ModelVersion, tenant_id: str | None = None) -> None:
        self.model_versions[record.id] = record
        if self._sql_enabled():
            self.session.merge(m.ModelVersionORM(id=record.id, tenant_id=tenant_id, model_id=record.model_id, version=record.version, purpose=record.purpose, status=record.status, approved_by=record.approved_by, approval_date=record.approval_date, governance_json=asdict(record)))
            self.session.commit()

    def _active(self, record: Any) -> bool:
        return getattr(record, "deleted_at", None) is None

    def get_user(self, user_id: str) -> User | None:
        if self._sql_enabled():
            row = self.session.get(m.UserORM, user_id)
            if row and row.deleted_at is None:
                user = User(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    email=row.email,
                    password_hash=row.password_hash,
                    roles=set(row.roles_json),
                    deleted_at=row.deleted_at,
                )
                self.users[user.id] = user
                self.users_by_email[user.email] = user.id
                return user
            return None
        user = self.users.get(user_id)
        if user and not user.deleted_at:
            return user
        return None

    def get_session(self, session_id: str) -> Session | None:
        if self._sql_enabled():
            row = self.session.get(m.SessionORM, session_id)
            if row and row.deleted_at is None:
                record = Session(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    user_id=row.user_id,
                    device_id=row.device_id or "unknown",
                    refresh_token_hash=row.refresh_token_hash,
                    revoked_at=row.revoked_at,
                )
                self.sessions[record.id] = record
                return record
            return None
        return self.sessions.get(session_id)

    def list_sessions_for_user(self, user_id: str, active_only: bool = True) -> list[Session]:
        if not self._sql_enabled():
            records = [s for s in self.sessions.values() if s.user_id == user_id]
            return [s for s in records if s.revoked_at is None] if active_only else records
        statement = select(m.SessionORM).where(m.SessionORM.user_id == user_id, m.SessionORM.deleted_at.is_(None))
        if active_only:
            statement = statement.where(m.SessionORM.revoked_at.is_(None))
        return [
            Session(
                id=row.id,
                tenant_id=row.tenant_id,
                user_id=row.user_id,
                device_id=row.device_id or "unknown",
                refresh_token_hash=row.refresh_token_hash,
                revoked_at=row.revoked_at,
            )
            for row in self.session.exec(statement).all()
        ]

    def get_consent(self, consent_id: str) -> ConsentRecord | None:
        if self._sql_enabled():
            row = self.session.get(m.ConsentRecordORM, consent_id)
            if row and row.deleted_at is None:
                record = ConsentRecord(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    user_id=row.user_id,
                    purpose=ConsentPurpose(row.purpose),
                    version=row.version,
                    granted=row.granted,
                    revoked_at=row.revoked_at,
                )
                self.consent[record.id] = record
                return record
            return None
        return self.consent.get(consent_id)

    def list_consent_for_user(self, user_id: str, active_only: bool = False) -> list[ConsentRecord]:
        if not self._sql_enabled():
            records = [c for c in self.consent.values() if c.user_id == user_id]
            return [c for c in records if c.granted and c.revoked_at is None] if active_only else records
        statement = select(m.ConsentRecordORM).where(
            m.ConsentRecordORM.user_id == user_id,
            m.ConsentRecordORM.deleted_at.is_(None),
        )
        if active_only:
            statement = statement.where(m.ConsentRecordORM.granted.is_(True), m.ConsentRecordORM.revoked_at.is_(None))
        return [
            ConsentRecord(
                id=row.id,
                tenant_id=row.tenant_id,
                user_id=row.user_id,
                purpose=ConsentPurpose(row.purpose),
                version=row.version,
                granted=row.granted,
                revoked_at=row.revoked_at,
            )
            for row in self.session.exec(statement).all()
        ]

    def list_consent_for_tenant(self, tenant_id: str, active_only: bool = False) -> list[ConsentRecord]:
        records = [c for c in self.consent.values() if c.tenant_id == tenant_id]
        if active_only:
            records = [c for c in records if c.granted and c.revoked_at is None]
        return records

    def get_image(self, image_id: str, user_id: str | None = None, tenant_id: str | None = None) -> ImageCapture | None:
        if self._sql_enabled():
            row = self.session.get(m.ImageCaptureORM, image_id)
            if row and row.deleted_at is None:
                if user_id and row.user_id != user_id:
                    return None
                if tenant_id and row.tenant_id != tenant_id:
                    return None
                record = ImageCapture(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    user_id=row.user_id,
                    checksum_sha256=row.checksum_sha256,
                    content_type=row.content_type,
                    size_bytes=row.size_bytes,
                    storage_ref=row.storage_ref_encrypted,
                    status=row.status,
                    deleted_at=row.deleted_at,
                )
                self.images[record.id] = record
                return record
            return None
        record = self.images.get(image_id)
        if record and self._active(record):
            if user_id and record.user_id != user_id:
                return None
            if tenant_id and record.tenant_id != tenant_id:
                return None
            return record
        return None

    def list_images_for_user(self, user_id: str, active_only: bool = True) -> list[dict[str, Any]]:
        if self._sql_enabled():
            statement = select(m.ImageCaptureORM).where(m.ImageCaptureORM.user_id == user_id)
            if active_only:
                statement = statement.where(m.ImageCaptureORM.deleted_at.is_(None), m.ImageCaptureORM.status != "deleted")
            return [self.redact_image(self._image_from_row(row)) for row in self.session.exec(statement).all()]
        records = [i for i in self.images.values() if i.user_id == user_id]
        if active_only:
            records = [i for i in records if i.deleted_at is None and i.status != "deleted"]
        return [self.redact_image(record) for record in records]

    def list_images_for_tenant(self, tenant_id: str, active_only: bool = True) -> list[dict[str, Any]]:
        if self._sql_enabled():
            statement = select(m.ImageCaptureORM).where(m.ImageCaptureORM.tenant_id == tenant_id)
            if active_only:
                statement = statement.where(m.ImageCaptureORM.deleted_at.is_(None), m.ImageCaptureORM.status != "deleted")
            return [self.redact_image(self._image_from_row(row)) for row in self.session.exec(statement).all()]
        records = [i for i in self.images.values() if i.tenant_id == tenant_id]
        if active_only:
            records = [i for i in records if i.deleted_at is None and i.status != "deleted"]
        return [self.redact_image(record) for record in records]

    def _image_from_row(self, row: Any) -> ImageCapture:
        return ImageCapture(
            id=row.id,
            tenant_id=row.tenant_id,
            user_id=row.user_id,
            checksum_sha256=row.checksum_sha256,
            content_type=row.content_type,
            size_bytes=row.size_bytes,
            storage_ref=row.storage_ref_encrypted,
            status=row.status,
            deleted_at=row.deleted_at,
        )

    def redact_image(self, record: ImageCapture) -> dict[str, Any]:
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "user_id": record.user_id,
            "checksum_sha256": record.checksum_sha256,
            "content_type": record.content_type,
            "size_bytes": record.size_bytes,
            "status": record.status,
            "deleted_at": record.deleted_at,
        }

    def redact_session(self, record: Session) -> dict[str, Any]:
        return {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "user_id": record.user_id,
            "device_id": record.device_id,
            "revoked": record.revoked_at is not None,
        }

    def get_analysis(self, job_id: str, user_id: str | None = None, tenant_id: str | None = None) -> AnalysisJob | None:
        if self._sql_enabled():
            row = self.session.get(m.AnalysisJobORM, job_id)
            if row and row.deleted_at is None:
                if user_id and row.user_id != user_id:
                    return None
                if tenant_id and row.tenant_id != tenant_id:
                    return None
                record = AnalysisJob(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    user_id=row.user_id,
                    image_id=row.image_id,
                    status=JobStatus(row.status),
                    model_version=row.model_version,
                    quality_score=row.quality_score,
                    lighting_score=row.lighting_score,
                    confidence=row.confidence,
                    uncertainty=row.uncertainty,
                    failure_reason=row.failure_reason,
                    result=row.result_json,
                )
                self.analysis_jobs[record.id] = record
                return record
            return None
        record = self.analysis_jobs.get(job_id)
        if record:
            if user_id and record.user_id != user_id:
                return None
            if tenant_id and record.tenant_id != tenant_id:
                return None
            return record
        return None

    def list_analysis_for_user(self, user_id: str) -> list[AnalysisJob]:
        if self._sql_enabled():
            rows = self.session.exec(select(m.AnalysisJobORM).where(m.AnalysisJobORM.user_id == user_id, m.AnalysisJobORM.deleted_at.is_(None))).all()
            return [self.get_analysis(row.id) for row in rows if self.get_analysis(row.id) is not None]
        return [job for job in self.analysis_jobs.values() if job.user_id == user_id]

    def list_analysis_for_tenant(self, tenant_id: str) -> list[AnalysisJob]:
        if self._sql_enabled():
            rows = self.session.exec(select(m.AnalysisJobORM).where(m.AnalysisJobORM.tenant_id == tenant_id, m.AnalysisJobORM.deleted_at.is_(None))).all()
            return [self.get_analysis(row.id) for row in rows if self.get_analysis(row.id) is not None]
        return [job for job in self.analysis_jobs.values() if job.tenant_id == tenant_id]

    def get_render(self, render_id: str, user_id: str | None = None, tenant_id: str | None = None) -> RenderJob | None:
        if self._sql_enabled():
            row = self.session.get(m.AuthenticRenderORM, render_id)
            if row and row.deleted_at is None:
                if user_id and row.user_id != user_id:
                    return None
                if tenant_id and row.tenant_id != tenant_id:
                    return None
                safety = self.get_render_safety_report(row.id) or {}
                record = RenderJob(
                    id=row.id,
                    tenant_id=row.tenant_id,
                    user_id=row.user_id,
                    analysis_id=row.analysis_id,
                    status=RenderStatus(row.status),
                    confidence=row.confidence,
                    uncertainty=row.uncertainty,
                    safety_report=safety,
                    rendered_ref=row.rendered_ref_encrypted,
                )
                self.render_jobs[record.id] = record
                return record
            return None
        record = self.render_jobs.get(render_id)
        if record:
            if user_id and record.user_id != user_id:
                return None
            if tenant_id and record.tenant_id != tenant_id:
                return None
            return record
        return None

    def list_renders_for_user(self, user_id: str) -> list[RenderJob]:
        if self._sql_enabled():
            rows = self.session.exec(select(m.AuthenticRenderORM).where(m.AuthenticRenderORM.user_id == user_id, m.AuthenticRenderORM.deleted_at.is_(None))).all()
            return [self.get_render(row.id) for row in rows if self.get_render(row.id) is not None]
        return [render for render in self.render_jobs.values() if render.user_id == user_id]

    def list_renders_for_tenant(self, tenant_id: str) -> list[RenderJob]:
        if self._sql_enabled():
            rows = self.session.exec(select(m.AuthenticRenderORM).where(m.AuthenticRenderORM.tenant_id == tenant_id, m.AuthenticRenderORM.deleted_at.is_(None))).all()
            return [self.get_render(row.id) for row in rows if self.get_render(row.id) is not None]
        return [render for render in self.render_jobs.values() if render.tenant_id == tenant_id]

    def get_render_safety_report(self, render_id: str) -> dict[str, Any] | None:
        record = self.render_jobs.get(render_id)
        if record:
            return record.safety_report
        if self._sql_enabled():
            row = self.session.exec(select(m.RenderSafetyReportORM).where(m.RenderSafetyReportORM.render_id == render_id)).first()
            if row:
                return row.report_json
        return None

    def list_audit_for_tenant(self, tenant_id: str) -> list[AuditEvent]:
        return [event for event in self.audit_events if event.tenant_id == tenant_id]

    def save_privacy_export(self, record: dict[str, Any]) -> None:
        self.generic_records.append({"kind": "privacy_export", "tenant_id": record.get("tenant_id"), "user_id": record.get("user_id"), "record": record})
        if self._sql_enabled():
            self.session.merge(m.DataExportRequestORM(id=record["id"], tenant_id=record["tenant_id"], user_id=record["user_id"], status=record.get("status", "queued"), export_json=record.get("data", {})))
            self.session.commit()

    def save_privacy_deletion(self, record: dict[str, Any]) -> None:
        self.generic_records.append({"kind": "privacy_deletion", "tenant_id": record.get("tenant_id"), "user_id": record.get("user_id"), "record": record})
        if self._sql_enabled():
            self.session.merge(m.DataDeletionRequestORM(id=record["id"], tenant_id=record["tenant_id"], user_id=record["user_id"], status=record.get("status", "queued"), policy_json=record))
            self.session.commit()

    def save_dataset_version(self, record: dict[str, Any], tenant_id: str | None = None) -> None:
        self.generic_records.append({"kind": "dataset_version", "tenant_id": tenant_id, "user_id": None, "record": record})
        if self._sql_enabled():
            self.session.merge(m.DatasetVersionORM(id=record["id"], tenant_id=tenant_id, version=record["version"], provenance_notes=record["provenance_notes"], dataset_json=record))
            self.session.commit()

    def save_bias_report(self, record: dict[str, Any], tenant_id: str | None = None) -> None:
        self.generic_records.append({"kind": "bias_report", "tenant_id": tenant_id, "user_id": None, "record": record})
        if self._sql_enabled():
            self.session.merge(m.BiasReportORM(id=record["id"], tenant_id=tenant_id, evaluation_scope=record["evaluation_scope"], report_json=record))
            self.session.commit()

    def save_incident(self, record: dict[str, Any], tenant_id: str | None = None) -> None:
        self.generic_records.append({"kind": "incident", "tenant_id": tenant_id, "user_id": None, "record": record})
        if self._sql_enabled():
            self.session.merge(m.IncidentORM(id=record["id"], tenant_id=tenant_id, severity=record["severity"], mitigation_status=record["mitigation_status"], incident_json=record))
            self.session.commit()

    def list_model_versions(self, tenant_id: str | None = None) -> list[ModelVersion]:
        records = list(self.model_versions.values())
        if records or not self._sql_enabled():
            return records
        statement = select(m.ModelVersionORM).where(m.ModelVersionORM.deleted_at.is_(None))
        if tenant_id:
            statement = statement.where(m.ModelVersionORM.tenant_id == tenant_id)
        return [ModelVersion(**row.governance_json) for row in self.session.exec(statement).all()]

    def list_dataset_versions(self, tenant_id: str | None = None) -> list[dict[str, Any]]:
        return [item["record"] for item in self.list_records("dataset_version", tenant_id=tenant_id)]

    def list_bias_reports(self, tenant_id: str | None = None) -> list[dict[str, Any]]:
        return [item["record"] for item in self.list_records("bias_report", tenant_id=tenant_id)]

    def list_incidents(self, tenant_id: str | None = None) -> list[dict[str, Any]]:
        return [item["record"] for item in self.list_records("incident", tenant_id=tenant_id)]

    def user_by_email(self, email: str) -> User | None:
        if email in self.users_by_email:
            return self.users[self.users_by_email[email]]
        if self._sql_enabled():
            row = self.session.exec(select(m.UserORM).where(m.UserORM.email == email, m.UserORM.deleted_at.is_(None))).first()
            if row:
                user = User(id=row.id, tenant_id=row.tenant_id, email=row.email, password_hash=row.password_hash, roles=set(row.roles_json), deleted_at=row.deleted_at)
                self.users[user.id] = user
                self.users_by_email[user.email] = user.id
                return user
        return None
