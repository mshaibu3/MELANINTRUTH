from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

NORMALIZED_TABLES = [
    "users", "sessions", "devices", "tenants", "tenant_members", "consent_records", "image_captures", "image_quality_reports", "lighting_analyses", "skin_analyses", "analysis_jobs", "authentic_renders", "render_safety_reports", "audit_logs", "security_events", "data_export_requests", "data_deletion_requests", "model_versions", "dataset_versions", "bias_reports", "incidents",
]


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class NormalizedTableSpec:
    name: str
    has_tenant_id: bool = True
    has_user_id: bool = True
    has_deleted_at: bool = True
    has_payload_json: bool = True


TABLE_SPECS = {name: NormalizedTableSpec(name=name) for name in NORMALIZED_TABLES}

try:
    from sqlalchemy import Column, JSON, UniqueConstraint
    from sqlmodel import Field, SQLModel
except ModuleNotFoundError:
    SQLModel = object  # type: ignore[assignment]
else:
    class TimestampMixin(SQLModel):
        created_at: datetime = Field(default_factory=utc_now, index=True)
        updated_at: datetime = Field(default_factory=utc_now)
        deleted_at: datetime | None = Field(default=None, index=True)

    class TenantORM(TimestampMixin, table=True):
        __tablename__ = "orm_tenants"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        name: str = Field(index=True)
        metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class UserORM(TimestampMixin, table=True):
        __tablename__ = "orm_users"
        __table_args__ = (UniqueConstraint("email", name="ux_orm_users_email"),)
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        email: str = Field(index=True)
        password_hash: str
        roles_json: list[str] = Field(default_factory=lambda: ["user"], sa_column=Column(JSON))
        metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class SessionORM(TimestampMixin, table=True):
        __tablename__ = "orm_sessions"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        user_id: str = Field(index=True)
        device_id: str | None = Field(default=None, index=True)
        refresh_token_hash: str = Field(index=True)
        revoked_at: datetime | None = Field(default=None, index=True)
        metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class DeviceORM(TimestampMixin, table=True):
        __tablename__ = "orm_devices"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        user_id: str = Field(index=True)
        label: str
        metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class TenantMemberORM(TimestampMixin, table=True):
        __tablename__ = "orm_tenant_members"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        user_id: str = Field(index=True)
        role: str = Field(default="member", index=True)
        metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class ConsentRecordORM(TimestampMixin, table=True):
        __tablename__ = "orm_consent_records"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        user_id: str = Field(index=True)
        purpose: str = Field(index=True)
        version: str
        granted: bool = Field(default=True, index=True)
        revoked_at: datetime | None = Field(default=None, index=True)
        metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class ImageCaptureORM(TimestampMixin, table=True):
        __tablename__ = "orm_image_captures"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        user_id: str = Field(index=True)
        checksum_sha256: str = Field(index=True)
        content_type: str
        size_bytes: int
        storage_ref_encrypted: str
        status: str = Field(default="available", index=True)
        metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class AnalysisJobORM(TimestampMixin, table=True):
        __tablename__ = "orm_analysis_jobs"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        user_id: str = Field(index=True)
        image_id: str = Field(index=True)
        status: str = Field(index=True)
        model_version: str
        quality_score: float = 0
        lighting_score: float = 0
        confidence: float = 0
        uncertainty: float = 1
        failure_reason: str | None = None
        result_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class AuthenticRenderORM(TimestampMixin, table=True):
        __tablename__ = "orm_authentic_renders"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        user_id: str = Field(index=True)
        analysis_id: str = Field(index=True)
        status: str = Field(index=True)
        confidence: float = 0
        uncertainty: float = 1
        rendered_ref_encrypted: str | None = None
        metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class RenderSafetyReportORM(TimestampMixin, table=True):
        __tablename__ = "orm_render_safety_reports"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        user_id: str = Field(index=True)
        render_id: str = Field(index=True)
        passed: bool = Field(index=True)
        risk_level: str = Field(index=True)
        report_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class AuditLogORM(TimestampMixin, table=True):
        __tablename__ = "orm_audit_logs"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str | None = Field(default=None, index=True)
        user_id: str | None = Field(default=None, index=True)
        event_type: str = Field(index=True)
        resource_type: str = Field(index=True)
        resource_id: str | None = Field(default=None, index=True)
        metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class SecurityEventORM(TimestampMixin, table=True):
        __tablename__ = "orm_security_events"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str | None = Field(default=None, index=True)
        user_id: str | None = Field(default=None, index=True)
        event_type: str = Field(index=True)
        resource_type: str = Field(index=True)
        resource_id: str | None = Field(default=None, index=True)
        metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class DataExportRequestORM(TimestampMixin, table=True):
        __tablename__ = "orm_data_export_requests"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        user_id: str = Field(index=True)
        status: str = Field(default="queued", index=True)
        export_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class DataDeletionRequestORM(TimestampMixin, table=True):
        __tablename__ = "orm_data_deletion_requests"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        user_id: str = Field(index=True)
        status: str = Field(default="queued", index=True)
        policy_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class ModelVersionORM(TimestampMixin, table=True):
        __tablename__ = "orm_model_versions"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str | None = Field(default=None, index=True)
        model_id: str = Field(index=True)
        version: str = Field(index=True)
        purpose: str
        status: str = Field(index=True)
        approved_by: str | None = None
        approval_date: datetime | None = None
        governance_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class DatasetVersionORM(TimestampMixin, table=True):
        __tablename__ = "orm_dataset_versions"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str | None = Field(default=None, index=True)
        version: str = Field(index=True)
        provenance_notes: str
        dataset_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class BiasReportORM(TimestampMixin, table=True):
        __tablename__ = "orm_bias_reports"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str | None = Field(default=None, index=True)
        evaluation_scope: str
        report_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class IncidentORM(TimestampMixin, table=True):
        __tablename__ = "orm_incidents"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str | None = Field(default=None, index=True)
        severity: str = Field(index=True)
        mitigation_status: str = Field(index=True)
        incident_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class ImageQualityReportORM(TimestampMixin, table=True):
        __tablename__ = "orm_image_quality_reports"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        user_id: str = Field(index=True)
        image_id: str = Field(index=True)
        report_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class LightingAnalysisORM(TimestampMixin, table=True):
        __tablename__ = "orm_lighting_analyses"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        user_id: str = Field(index=True)
        image_id: str = Field(index=True)
        report_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    class SkinAnalysisORM(TimestampMixin, table=True):
        __tablename__ = "orm_skin_analyses"
        id: str = Field(default_factory=new_uuid, primary_key=True)
        tenant_id: str = Field(index=True)
        user_id: str = Field(index=True)
        image_id: str = Field(index=True)
        report_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
