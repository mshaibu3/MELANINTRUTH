from __future__ import annotations

from api_helpers import auth_header, complete_image, grant, register_and_login


def test_image_upload_redaction_and_cross_user(client):
    token, _, _ = register_and_login(client, email="image@example.com")
    assert client.post("/images/upload-request", json={}).status_code == 401
    no_consent = client.post("/images/upload-request", headers=auth_header(token), json={"content_type": "image/png", "size_bytes": 128, "checksum_sha256": "d" * 64})
    assert no_consent.status_code == 403
    grant(client, token, "image_processing")
    invalid = client.post("/images/upload-request", headers=auth_header(token), json={"content_type": "text/plain", "size_bytes": 128, "checksum_sha256": "d" * 64})
    assert invalid.status_code == 422
    oversized = client.post("/images/upload-request", headers=auth_header(token), json={"content_type": "image/png", "size_bytes": 20_000_000, "checksum_sha256": "d" * 64})
    assert oversized.status_code == 422
    image_id = complete_image(client, token, checksum="e" * 64)
    metadata = client.get(f"/images/{image_id}", headers=auth_header(token)).json()
    assert "storage_ref" not in metadata and "storage_ref_encrypted" not in metadata
    other_token, _, _ = register_and_login(client, email="other@example.com")
    assert client.get(f"/images/{image_id}", headers=auth_header(other_token)).status_code == 404
    assert client.delete(f"/images/{image_id}", headers=auth_header(token)).status_code == 200
