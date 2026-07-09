from __future__ import annotations

from api_helpers import auth_header, complete_image, grant, register_and_login


def test_privacy_export_delete_blocks_future_processing(client):
    token, _, _ = register_and_login(client, email="privacy@example.com")
    grant(client, token, "image_processing")
    image_id = complete_image(client, token, checksum="2" * 64)
    export = client.post("/privacy/export", headers=auth_header(token)).json()
    data = client.get(f"/privacy/export/{export['request_id']}", headers=auth_header(token)).json()["data"]
    assert "storage_ref" not in str(data) and image_id in str(data)
    deletion = client.post("/privacy/delete", headers=auth_header(token))
    assert deletion.status_code == 200
    blocked = client.post("/images/upload-request", headers=auth_header(token), json={"content_type": "image/png", "size_bytes": 128, "checksum_sha256": "3" * 64})
    assert blocked.status_code == 403
