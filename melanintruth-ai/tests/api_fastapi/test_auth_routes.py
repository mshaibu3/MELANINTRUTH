from __future__ import annotations

from api_helpers import auth_header, error_code, register_and_login


def test_auth_lifecycle_and_protected_rejections(client):
    token, refresh, session_id = register_and_login(client)
    duplicate = client.post("/auth/register", json={"email": "user@example.com", "password": "CorrectHorseBatteryStaple123!"})
    assert duplicate.status_code == 409
    assert error_code(duplicate) == "VALIDATION_ERROR"
    failed = client.post("/auth/login", json={"email": "user@example.com", "password": "wrong"})
    assert failed.status_code == 401
    assert error_code(failed) == "AUTH_REQUIRED"
    rotated = client.post("/auth/refresh", json={"refresh_token": refresh, "session_id": session_id})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != refresh
    assert client.get("/auth/sessions", headers=auth_header(token)).status_code == 200
    assert client.get("/auth/sessions").status_code == 401
    assert client.get("/auth/sessions", headers=auth_header("bad-token")).status_code == 401
    logout = client.post("/auth/logout", headers=auth_header(token), json={"session_id": session_id})
    assert logout.status_code == 200


def test_deleted_account_blocks_processing(client):
    token, _, _ = register_and_login(client, email="delete@example.com")
    assert client.post("/auth/account-deletion-request", headers=auth_header(token)).status_code == 200
    blocked = client.post("/images/upload-request", headers=auth_header(token), json={"content_type": "image/png", "size_bytes": 128, "checksum_sha256": "b" * 64})
    assert blocked.status_code == 403
