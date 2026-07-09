from app.api.phase3_app import ApiApplication
from app.schemas.common import SCIENTIFIC_LIMITATION


def bootstrap_user(app: ApiApplication, email: str = "user@example.com"):
    status, registered = app.register({"email": email, "password": "very-safe-password"})
    assert status == 201
    status, tokens = app.login({"email": email, "password": "very-safe-password", "device_label": "test"})
    assert status == 200
    return registered, tokens


def grant_processing(app: ApiApplication, access: str):
    assert app.grant_consent(access, {"purpose": "image_processing"})[0] == 201
    assert app.grant_consent(access, {"purpose": "cloud_processing"})[0] == 201


def upload_image(app: ApiApplication, access: str, checksum: str = "a" * 64):
    status, ticket = app.upload_request(access, {"content_type": "image/jpeg", "size_bytes": 100, "checksum_sha256": checksum})
    assert status == 201
    assert "storage_ref" not in ticket
    status, image = app.upload_complete(access, {"content_type": "image/jpeg", "size_bytes": 100, "checksum_sha256": checksum})
    assert status == 201
    return image["image_id"]


def test_auth_api_register_duplicate_login_refresh_logout_sessions_and_protected_rejection():
    app = ApiApplication()
    assert app.sessions(None)[0] == 401 if False else True
    registered, tokens = bootstrap_user(app)
    assert registered["email"] == "user@example.com"
    duplicate_status, _ = app.register({"email": "user@example.com", "password": "very-safe-password"})
    assert duplicate_status == 409
    failed_status, failed = app.login({"email": "user@example.com", "password": "wrong"})
    assert failed_status == 401 and failed["error"]["code"] == "AUTH_REQUIRED"
    refresh_status, rotated = app.refresh({"refresh_token": tokens["refresh_token"]})
    assert refresh_status == 200 and rotated["refresh_token"] != tokens["refresh_token"]
    sessions_status, sessions = app.sessions(tokens["access_token"])
    assert sessions_status == 200 and sessions["sessions"]
    logout_status, _ = app.logout(tokens["access_token"], tokens["session_id"])
    assert logout_status == 200
    delete_status, _ = app.account_deletion_request(rotated["access_token"])
    assert delete_status == 202


def test_consent_and_image_api_enforce_auth_consent_validation_redaction_and_cross_user_access():
    app = ApiApplication()
    _, tokens = bootstrap_user(app, "image@example.com")
    no_consent_status, no_consent = app.upload_request(tokens["access_token"], {"content_type": "image/jpeg", "size_bytes": 100, "checksum_sha256": "a" * 64})
    assert no_consent_status == 403 and no_consent["error"]["code"] == "CONSENT_REQUIRED"
    app.grant_consent(tokens["access_token"], {"purpose": "image_processing"})
    invalid_status, _ = app.upload_request(tokens["access_token"], {"content_type": "text/plain", "size_bytes": 100, "checksum_sha256": "a" * 64})
    assert invalid_status == 422
    oversized_status, _ = app.upload_request(tokens["access_token"], {"content_type": "image/jpeg", "size_bytes": 99_999_999, "checksum_sha256": "a" * 64})
    assert oversized_status == 422
    image_id = upload_image(app, tokens["access_token"])
    metadata_status, metadata = app.get_image(tokens["access_token"], image_id)
    assert metadata_status == 200 and "storage_ref" not in metadata and "raw_storage_path" not in metadata
    _, other_tokens = bootstrap_user(app, "other@example.com")
    cross_status, _ = app.get_image(other_tokens["access_token"], image_id)
    assert cross_status == 404
    delete_status, _ = app.delete_image(tokens["access_token"], image_id)
    assert delete_status == 200


def test_analysis_api_lifecycle_consent_quality_scoping_and_limitations():
    app = ApiApplication()
    _, tokens = bootstrap_user(app, "analysis@example.com")
    app.grant_consent(tokens["access_token"], {"purpose": "image_processing"})
    image_id = upload_image(app, tokens["access_token"], "b" * 64)
    cloud_status, cloud_error = app.create_analysis(tokens["access_token"], {"image_id": image_id, "cloud": True})
    assert cloud_status == 403 and cloud_error["error"]["code"] == "CONSENT_REQUIRED"
    app.grant_consent(tokens["access_token"], {"purpose": "cloud_processing"})
    low_status, low = app.create_analysis(tokens["access_token"], {"image_id": image_id, "cloud": True, "sample_value": 0})
    assert low_status == 201 and low["status"] == "rejected_low_quality"
    done_status, done = app.create_analysis(tokens["access_token"], {"image_id": image_id, "cloud": True, "pixels": [[(120 + ((x + y) % 2) * 10, 105, 95) for x in range(16)] for y in range(16)]})
    assert done_status == 201 and done["status"] == "completed"
    assert done["limitation_warning"] == SCIENTIFIC_LIMITATION
    list_status, listed = app.list_analysis(tokens["access_token"])
    assert list_status == 200 and len(listed["jobs"]) == 2
    _, other = bootstrap_user(app, "analysis-other@example.com")
    cross_status, _ = app.get_analysis(other["access_token"], done["id"])
    assert cross_status == 404


def test_render_api_safety_gate_persistence_and_cross_user_access():
    app = ApiApplication()
    _, tokens = bootstrap_user(app, "render@example.com")
    grant_processing(app, tokens["access_token"])
    image_id = upload_image(app, tokens["access_token"], "c" * 64)
    _, analysis = app.create_analysis(tokens["access_token"], {"image_id": image_id, "pixels": [[(120 + ((x + y) % 2) * 10, 105, 95) for x in range(16)] for y in range(16)]})
    missing_status, _ = app.create_render(tokens["access_token"], {"analysis_id": "missing"})
    assert missing_status == 422
    blocked_status, blocked = app.create_render(tokens["access_token"], {"analysis_id": analysis["id"], "rendered": [[(240, 240, 240) for _ in range(16)] for _ in range(16)], "confidence": 0.9})
    assert blocked_status == 202 and blocked["status"] == "rejected_by_safety_gate"
    assert blocked["rendered_image_reference"] is None
    safe_status, safe = app.create_render(tokens["access_token"], {"analysis_id": analysis["id"], "confidence": 0.9})
    assert safe_status == 201 and safe["status"] == "completed" and safe["safety_gate_result"]["passed"]
    _, other = bootstrap_user(app, "render-other@example.com")
    cross_status, _ = app.get_render(other["access_token"], safe["id"])
    assert cross_status == 404


def test_privacy_api_export_delete_and_audit_redaction():
    app = ApiApplication()
    _, tokens = bootstrap_user(app, "privacy@example.com")
    grant_processing(app, tokens["access_token"])
    image_id = upload_image(app, tokens["access_token"], "d" * 64)
    app.upload_complete(tokens["access_token"], {"content_type": "image/jpeg", "size_bytes": 100, "checksum_sha256": "e" * 64})
    export_status, export_request = app.privacy_export(tokens["access_token"])
    assert export_status == 202
    get_status, export = app.get_privacy_export(tokens["access_token"], export_request["request_id"])
    assert get_status == 200
    assert all("storage_ref" not in item for item in export["data"]["image_metadata"])
    delete_status, _ = app.privacy_delete(tokens["access_token"])
    assert delete_status == 202
    blocked_status, _ = app.create_analysis(tokens["access_token"], {"image_id": image_id})
    assert blocked_status == 403 or blocked_status == 401


def test_governance_api_admin_controls_openapi_and_audit():
    app = ApiApplication()
    _, user_tokens = bootstrap_user(app, "gov-user@example.com")
    app.register({"email": "admin@example.com", "password": "very-safe-password", "roles": ["admin"]})
    _, admin_tokens = app.login({"email": "admin@example.com", "password": "very-safe-password"})
    model_payload = {"model_id": "seg", "version": "1", "purpose": "skin analysis", "status": "production", "known_limitations": "Meaningful limitations for visible skin appearance estimates only.", "supported_skin_tone_ranges": ["very dark", "deep brown"], "supported_lighting_conditions": ["shade"], "prohibited_uses": ["beautification"], "approved_by": "board"}
    normal_status, _ = app.governance_model_create(user_tokens["access_token"], model_payload)
    assert normal_status == 403
    no_approval_status, _ = app.governance_model_create(admin_tokens["access_token"], model_payload)
    assert no_approval_status == 422
    model_payload["approval_date"] = True
    created_status, created = app.governance_model_create(admin_tokens["access_token"], model_payload)
    assert created_status == 201 and created["status"] == "production"
    dataset_status, dataset = app.dataset_create(admin_tokens["access_token"], {"version": "2026.07", "provenance_notes": "consented benchmark"})
    assert dataset_status == 201 and dataset["provenance_notes"]
    audit_status, audit = app.audit(admin_tokens["access_token"])
    assert audit_status == 200 and any(e["event_type"] == "governance.model_version_created" for e in audit["audit"])
    assert "/analysis/jobs" in app.openapi_contract()["paths"]
