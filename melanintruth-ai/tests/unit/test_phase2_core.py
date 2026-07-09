from datetime import datetime, timezone

import pytest

from app.backend.audit import AuditService
from app.backend.auth import AuthService
from app.backend.consent import ConsentService
from app.backend.entities import ConsentPurpose, JobStatus, ModelVersion, RenderStatus
from app.backend.errors import AuthenticationError, AuthorizationError, ConflictError, ValidationError
from app.backend.governance import GovernanceService
from app.backend.image_service import ImageService
from app.backend.privacy import PrivacyService
from app.backend.repository import InMemoryRepository
from app.backend.security import hash_password, verify_password
from app.backend.vision import SafetyGate, sample_image
from app.backend.analysis import AnalysisService
from app.backend.rendering import RenderService


def services():
    repo = InMemoryRepository()
    audit = AuditService(repo)
    auth = AuthService(repo, audit)
    consent = ConsentService(repo, audit)
    images = ImageService(repo, audit, consent)
    analysis = AnalysisService(repo, audit, consent, images)
    rendering = RenderService(repo, audit, consent)
    privacy = PrivacyService(repo, audit)
    governance = GovernanceService(repo, audit)
    return repo, audit, auth, consent, images, analysis, rendering, privacy, governance


def grant_required(consent, user_id):
    consent.grant(user_id, ConsentPurpose.IMAGE_PROCESSING)
    consent.grant(user_id, ConsentPurpose.CLOUD_PROCESSING)


def test_password_hashing_is_not_plaintext():
    encoded = hash_password("very-safe-password")
    assert encoded != "very-safe-password"
    assert verify_password("very-safe-password", encoded)


def test_successful_registration_duplicate_login_failed_login_refresh_logout_and_admin_rejection():
    repo, _, auth, _, _, _, _, _, governance = services()
    user = auth.register("A@Example.com", "very-safe-password")
    assert user.email == "a@example.com"
    with pytest.raises(ConflictError):
        auth.register("a@example.com", "very-safe-password")
    tokens = auth.login("a@example.com", "very-safe-password", "phone")
    assert tokens["access_token"].count(".") == 2
    with pytest.raises(AuthenticationError):
        auth.login("a@example.com", "wrong-password", "phone")
    rotated = auth.refresh(tokens["session_id"], tokens["refresh_token"])
    assert rotated["refresh_token"] != tokens["refresh_token"]
    with pytest.raises(AuthenticationError):
        auth.refresh(tokens["session_id"], tokens["refresh_token"])
    auth.logout(user.id, tokens["session_id"])
    assert repo.sessions[tokens["session_id"]].revoked_at is not None
    with pytest.raises(AuthorizationError):
        governance.create_model_version(user.id, ModelVersion(model_id="m", version="1", purpose="test", status="draft", known_limitations="meaningful limitations for visible skin only", supported_skin_tone_ranges=["all"], supported_lighting_conditions=["even"], prohibited_uses=["beautification"]))


def test_consent_enforced_service_level_revocation_and_model_improvement_exclusion():
    _, _, auth, consent, images, analysis, _, _, _ = services()
    user = auth.register("c@example.com", "very-safe-password")
    with pytest.raises(AuthorizationError):
        images.request_upload(user.id, "image/jpeg", 100, "a" * 64)
    image_consent = consent.grant(user.id, ConsentPurpose.IMAGE_PROCESSING)
    ticket = images.request_upload(user.id, "image/jpeg", 100, "a" * 64)
    image = images.complete_upload(user.id, ticket, "image/jpeg", 100)
    with pytest.raises(AuthorizationError):
        analysis.create_job(user.id, image.id, sample_image(), cloud=True)
    assert consent.export_model_improvement_records(user.id) == []
    consent.revoke(user.id, image_consent.id)
    with pytest.raises(AuthorizationError):
        images.request_upload(user.id, "image/jpeg", 100, "b" * 64)


def test_secure_image_upload_validation_deletion_and_metadata_redaction():
    repo, _, auth, consent, images, _, _, _, _ = services()
    user = auth.register("i@example.com", "very-safe-password")
    consent.grant(user.id, ConsentPurpose.IMAGE_PROCESSING)
    with pytest.raises(ValidationError):
        images.request_upload(user.id, "text/plain", 100, "a" * 64)
    with pytest.raises(ValidationError):
        images.request_upload(user.id, "image/png", 99_999_999, "a" * 64)
    ticket = images.request_upload(user.id, "image/png", 100, "a" * 64)
    image = images.complete_upload(user.id, ticket, "image/png", 100)
    meta = images.public_metadata(user.id, image.id)
    assert "storage_ref" not in meta and "raw_storage_path" not in meta
    images.delete(user.id, image.id)
    assert any(e.event_type == "image.deleted" for e in repo.audit_events)


def test_analysis_lifecycle_completed_and_low_quality_rejected():
    _, _, auth, consent, images, analysis, _, _, _ = services()
    user = auth.register("an@example.com", "very-safe-password")
    grant_required(consent, user.id)
    ticket = images.request_upload(user.id, "image/jpeg", 100, "c" * 64)
    image = images.complete_upload(user.id, ticket, "image/jpeg", 100)
    low = analysis.create_job(user.id, image.id, sample_image(0), cloud=True)
    assert low.status == JobStatus.REJECTED_LOW_QUALITY
    textured = [[(120 + ((x + y) % 2) * 10, 105, 95) for x in range(16)] for y in range(16)]
    done = analysis.create_job(user.id, image.id, textured, cloud=True)
    assert done.status == JobStatus.COMPLETED
    assert done.result["confidence_score"] == done.confidence
    assert "limitation_warning" in done.result


def test_render_lifecycle_requires_completed_analysis_and_blocks_unsafe_outputs():
    repo, _, auth, consent, images, analysis, rendering, _, _ = services()
    user = auth.register("r@example.com", "very-safe-password")
    grant_required(consent, user.id)
    ticket = images.request_upload(user.id, "image/jpeg", 100, "d" * 64)
    image = images.complete_upload(user.id, ticket, "image/jpeg", 100)
    with pytest.raises(ValidationError):
        rendering.create_render(user.id, "missing", sample_image())
    textured = [[(120 + ((x + y) % 2) * 10, 105, 95) for x in range(16)] for y in range(16)]
    job = analysis.create_job(user.id, image.id, textured, cloud=True)
    shifted = sample_image(220)
    blocked = rendering.create_render(user.id, job.id, textured, shifted, confidence=0.9)
    assert blocked.status == RenderStatus.REJECTED_BY_SAFETY_GATE
    assert not blocked.safety_report["passed"]
    with pytest.raises(ValidationError):
        rendering.public_result(user.id, blocked.id)
    good = rendering.create_render(user.id, job.id, textured, textured, confidence=0.9)
    assert good.status == RenderStatus.COMPLETED
    assert any(e.event_type == "render.completed" for e in repo.audit_events)


def test_safety_gate_detects_tone_smoothing_low_confidence_and_histogram_shift():
    gate = SafetyGate()
    original = [[(80 + ((x + y) % 2) * 80, 70, 60) for x in range(16)] for y in range(16)]
    smoothed = sample_image(110)
    report = gate.evaluate(original, smoothed, confidence=0.4)
    assert not report["passed"]
    assert "confidence_threshold" in report["failed_checks"]
    assert "excessive_smoothing" in report["failed_checks"] or "texture_similarity" in report["failed_checks"]
    assert report["risk_level"] == "blocked"


def test_audit_redacts_tokens_passwords_and_raw_paths():
    repo, audit, *_ = services()
    audit.record("test", "image", "1", "u", "t", {"password": "x", "refresh_token": "secret", "raw_storage_path": "s3://raw", "safe": "ok"})
    assert repo.audit_events[-1].metadata == {"safe": "ok"}


def test_privacy_export_is_tenant_scoped_and_deletion_revokes_processing():
    repo, _, auth, consent, images, analysis, _, privacy, _ = services()
    user = auth.register("p@example.com", "very-safe-password")
    other = auth.register("other@example.com", "very-safe-password")
    grant_required(consent, user.id)
    grant_required(consent, other.id)
    user_tokens = auth.login("p@example.com", "very-safe-password", "phone")
    ticket = images.request_upload(user.id, "image/jpeg", 100, "e" * 64)
    image = images.complete_upload(user.id, ticket, "image/jpeg", 100)
    images.complete_upload(other.id, images.request_upload(other.id, "image/jpeg", 100, "f" * 64), "image/jpeg", 100)
    exported = privacy.export_user_data(user.id)
    assert all(item["id"] == image.id for item in exported["image_metadata"])
    privacy.delete_user_data(user.id)
    assert repo.sessions[user_tokens["session_id"]].revoked_at is not None
    with pytest.raises(AuthorizationError):
        analysis.create_job(user.id, image.id, sample_image(), cloud=True)
    assert any(e.event_type == "privacy.deletion_completed" for e in repo.audit_events)


def test_governance_admin_model_release_controls_and_audit():
    repo, _, auth, _, _, _, _, _, governance = services()
    admin = auth.register("admin@example.com", "very-safe-password", roles={"admin"})
    with pytest.raises(ValidationError):
        governance.create_model_version(admin.id, ModelVersion(model_id="seg", version="1", purpose="skin segmentation", status="draft", known_limitations="short", supported_skin_tone_ranges=["very dark", "deep brown"], supported_lighting_conditions=["shade"], prohibited_uses=["beautification"]))
    with pytest.raises(ValidationError):
        governance.create_model_version(admin.id, ModelVersion(model_id="seg", version="1", purpose="skin segmentation", status="production", known_limitations="Meaningful limitations for visible skin appearance estimation only.", supported_skin_tone_ranges=["very dark", "deep brown"], supported_lighting_conditions=["shade"], prohibited_uses=["beautification"]))
    model = governance.create_model_version(admin.id, ModelVersion(model_id="seg", version="1", purpose="skin segmentation", status="production", approved_by="board", approval_date=datetime.now(timezone.utc), evaluation_summary="passed fairness slices", known_limitations="Meaningful limitations for visible skin appearance estimation only.", supported_skin_tone_ranges=["very dark", "deep brown"], supported_lighting_conditions=["shade"], prohibited_uses=["beautification", "race inference"]))
    assert model.id in repo.model_versions
    assert any(e.event_type == "governance.model_version_created" for e in repo.audit_events)
