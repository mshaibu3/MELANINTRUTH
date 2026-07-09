from app.backend.audit import AuditService
from app.backend.auth import AuthService
from app.backend.consent import ConsentService
from app.backend.errors import AuthorizationError
from app.backend.image_service import ImageService
from app.backend.repository import InMemoryRepository


def test_analysis_upload_fails_without_consent():
    repo = InMemoryRepository()
    audit = AuditService(repo)
    auth = AuthService(repo, audit)
    consent = ConsentService(repo, audit)
    images = ImageService(repo, audit, consent)
    user = auth.register("api@example.com", "very-safe-password")
    try:
        images.request_upload(user.id, "image/jpeg", 100, "a" * 64)
        raised = False
    except AuthorizationError:
        raised = True
    assert raised


def test_logs_do_not_contain_raw_image_data_or_tokens():
    repo = InMemoryRepository()
    audit = AuditService(repo)
    audit.record("x", "image", "id", "u", "t", {"raw_image": "bytes", "access_token": "secret", "safe": "ok"})
    assert repo.audit_events[-1].metadata == {"safe": "ok"}
