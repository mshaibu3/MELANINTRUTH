from __future__ import annotations

from api_helpers import auth_header, complete_image, grant, register_and_login


def test_security_redaction_for_tokens_passwords_and_paths(client):
    token, _, _ = register_and_login(client, email="redact@example.com")
    grant(client, token, "image_processing")
    image_id = complete_image(client, token, checksum="4" * 64)
    response_text = client.get(f"/images/{image_id}", headers=auth_header(token)).text
    assert token not in response_text
    assert "CorrectHorseBatteryStaple" not in response_text
    assert "storage_ref" not in response_text and "encrypted_storage" not in response_text
