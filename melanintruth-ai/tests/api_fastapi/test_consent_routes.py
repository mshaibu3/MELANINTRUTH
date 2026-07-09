from __future__ import annotations

from api_helpers import auth_header, error_code, grant, register_and_login


def test_consent_grant_revoke_and_cloud_block(client):
    token, _, _ = register_and_login(client, email="consent@example.com")
    image = grant(client, token, "image_processing")
    assert image.status_code == 200
    assert grant(client, token, "cloud_processing").status_code == 200
    revoke = client.patch(f"/consent/{image.json()['id']}/revoke", headers=auth_header(token))
    assert revoke.status_code == 200
    upload = client.post("/images/upload-request", headers=auth_header(token), json={"content_type": "image/png", "size_bytes": 128, "checksum_sha256": "c" * 64})
    assert upload.status_code == 403
    assert error_code(upload) == "CONSENT_REQUIRED"
    assert client.get("/consent", headers=auth_header(token)).status_code == 200
