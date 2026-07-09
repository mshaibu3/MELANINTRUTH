from __future__ import annotations

from types import SimpleNamespace

from app.backend.audit import AuditService
from app.backend.entities import AnalysisJob, AuditEvent, ConsentPurpose, ConsentRecord, ImageCapture, ModelVersion, RenderJob, Session, User
from app.db.repositories.sqlmodel_runtime import SQLModelRepository
import app.db.repositories.sqlmodel_runtime as sqlmodel_runtime


def test_sqlmodel_repository_persist_record_keeps_service_maps_without_sql_session():
    repo = SQLModelRepository(session=None)
    user = User(id="user-1", tenant_id="tenant-1", email="phase37@example.com", password_hash="hash", roles={"user"})
    repo.persist_record("user", user, tenant_id=user.tenant_id, user_id=user.id)
    assert repo.user_by_email("phase37@example.com") == user
    assert repo.users[user.id].tenant_id == "tenant-1"


def test_sqlmodel_repository_audit_list_persists_redacted_events_without_sql_session():
    repo = SQLModelRepository(session=None)
    audit = AuditService(repo)
    audit.record(
        actor_user_id="user-1",
        tenant_id="tenant-1",
        event_type="image.upload",
        resource_type="image",
        resource_id="image-1",
        metadata={"token": "secret", "storage_path": "/raw/private/path", "safe": "ok"},
    )
    assert len(repo.audit_events) == 1
    event: AuditEvent = repo.audit_events[0]
    assert "token" not in event.metadata
    assert "storage_path" not in event.metadata
    assert event.metadata["safe"] == "ok"


def test_sqlmodel_repository_read_methods_scope_and_redact_core_aggregates():
    repo = SQLModelRepository(session=None)
    user = User(id="user-read", tenant_id="tenant-read", email="read@example.com", password_hash="hash", roles={"user"})
    session = Session(id="session-read", tenant_id=user.tenant_id, user_id=user.id, device_id="device", refresh_token_hash="token-hash")
    consent = ConsentRecord(id="consent-read", tenant_id=user.tenant_id, user_id=user.id, purpose=ConsentPurpose.IMAGE_PROCESSING, version="v1", granted=True)
    image = ImageCapture(id="image-read", tenant_id=user.tenant_id, user_id=user.id, checksum_sha256="a" * 64, content_type="image/png", size_bytes=123, storage_ref="internal/raw/path")
    analysis = AnalysisJob(id="analysis-read", tenant_id=user.tenant_id, user_id=user.id, image_id=image.id, confidence=0.9, uncertainty=0.1, lighting_score=0.8, quality_score=0.7)
    render = RenderJob(id="render-read", tenant_id=user.tenant_id, user_id=user.id, analysis_id=analysis.id, safety_report={"passed": True, "risk_level": "low"})
    model = ModelVersion(model_id="skin", version="1", purpose="analysis", status="candidate", known_limitations="lighting dependent", supported_skin_tone_ranges=["deep"], supported_lighting_conditions=["d65"], prohibited_uses=["beautification"])
    for kind, record in [("user", user), ("session", session), ("consent", consent), ("image", image), ("analysis", analysis), ("render", render), ("model_version", model)]:
        repo.persist_record(kind, record, tenant_id=user.tenant_id, user_id=user.id)
    assert repo.get_user(user.id) == user
    assert repo.get_session(session.id) == session
    assert repo.get_consent(consent.id) == consent
    assert repo.get_image(image.id, user_id=user.id, tenant_id=user.tenant_id) == image
    assert repo.get_image(image.id, user_id="other") is None
    assert repo.get_analysis(analysis.id, user_id=user.id) == analysis
    assert repo.get_render(render.id, tenant_id=user.tenant_id) == render
    redacted_image = repo.list_images_for_user(user.id)[0]
    redacted_session = repo.redact_session(session)
    assert "storage_ref" not in redacted_image and "internal/raw/path" not in str(redacted_image)
    assert "refresh_token_hash" not in redacted_session and "token-hash" not in str(redacted_session)
    assert repo.list_model_versions()[0].model_id == "skin"


def test_sqlmodel_repository_generic_governance_and_privacy_reads():
    repo = SQLModelRepository(session=None)
    export = {"id": "export-1", "tenant_id": "tenant-a", "user_id": "user-a", "status": "completed", "data": {"safe": True}}
    deletion = {"id": "delete-1", "tenant_id": "tenant-a", "user_id": "user-a", "status": "completed"}
    dataset = {"id": "dataset-1", "version": "v1", "provenance_notes": "explicit opt-in only"}
    bias = {"id": "bias-1", "evaluation_scope": "deep brown skin and low light"}
    incident = {"id": "incident-1", "severity": "high", "mitigation_status": "contained"}
    repo.persist_record("privacy_export", export, tenant_id="tenant-a", user_id="user-a")
    repo.persist_record("privacy_deletion", deletion, tenant_id="tenant-a", user_id="user-a")
    repo.persist_record("dataset_version", dataset, tenant_id="tenant-a")
    repo.persist_record("bias_report", bias, tenant_id="tenant-a")
    repo.persist_record("incident", incident, tenant_id="tenant-a")
    assert repo.list_records("privacy_export", tenant_id="tenant-a", user_id="user-a")[0]["record"] == export
    assert repo.list_records("privacy_deletion", tenant_id="tenant-a", user_id="user-a")[0]["record"] == deletion
    assert repo.list_dataset_versions("tenant-a") == [dataset]
    assert repo.list_bias_reports("tenant-a") == [bias]
    assert repo.list_incidents("tenant-a") == [incident]


class _FakeSqlSession:
    def __init__(self, rows):
        self.rows = rows

    def get(self, model, key):
        return self.rows.get((model, key))


def test_sqlmodel_repository_prefers_sql_reads_for_core_getters(monkeypatch):
    class FakeModels:
        UserORM = object()
        SessionORM = object()
        ConsentRecordORM = object()
        ImageCaptureORM = object()
        AnalysisJobORM = object()
        AuthenticRenderORM = object()

    rows = {
        (FakeModels.UserORM, "sql-user"): SimpleNamespace(id="sql-user", tenant_id="tenant-sql", email="sql@example.com", password_hash="hash", roles_json=["user"], deleted_at=None),
        (FakeModels.SessionORM, "sql-session"): SimpleNamespace(id="sql-session", tenant_id="tenant-sql", user_id="sql-user", device_id="device", refresh_token_hash="hash", revoked_at=None, deleted_at=None),
        (FakeModels.ConsentRecordORM, "sql-consent"): SimpleNamespace(id="sql-consent", tenant_id="tenant-sql", user_id="sql-user", purpose="image_processing", version="v1", granted=True, revoked_at=None, deleted_at=None),
        (FakeModels.ImageCaptureORM, "sql-image"): SimpleNamespace(id="sql-image", tenant_id="tenant-sql", user_id="sql-user", checksum_sha256="a" * 64, content_type="image/png", size_bytes=100, storage_ref_encrypted="raw-secret", status="available", deleted_at=None),
        (FakeModels.AnalysisJobORM, "sql-analysis"): SimpleNamespace(id="sql-analysis", tenant_id="tenant-sql", user_id="sql-user", image_id="sql-image", status="completed", model_version="baseline", quality_score=0.8, lighting_score=0.7, confidence=0.9, uncertainty=0.1, failure_reason=None, result_json={"visible": True}, deleted_at=None),
        (FakeModels.AuthenticRenderORM, "sql-render"): SimpleNamespace(id="sql-render", tenant_id="tenant-sql", user_id="sql-user", analysis_id="sql-analysis", status="completed", confidence=0.9, uncertainty=0.1, rendered_ref_encrypted="render-secret", deleted_at=None),
    }
    monkeypatch.setattr(sqlmodel_runtime, "SQLSession", object)
    monkeypatch.setattr(sqlmodel_runtime, "m", FakeModels, raising=False)
    repo = SQLModelRepository(session=_FakeSqlSession(rows))
    repo.get_render_safety_report = lambda render_id: {"passed": True}
    repo.users["sql-user"] = User(id="sql-user", tenant_id="wrong", email="wrong@example.com", password_hash="wrong")
    assert repo.get_user("sql-user").tenant_id == "tenant-sql"
    assert repo.get_session("sql-session").refresh_token_hash == "hash"
    assert repo.get_consent("sql-consent").purpose == ConsentPurpose.IMAGE_PROCESSING
    assert repo.get_image("sql-image", tenant_id="tenant-sql").storage_ref == "raw-secret"
    assert repo.get_analysis("sql-analysis", user_id="sql-user").confidence == 0.9
    assert repo.get_render("sql-render", user_id="sql-user").rendered_ref == "render-secret"
