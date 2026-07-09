from __future__ import annotations

import importlib
import os

import pytest

SCIENTIFIC_LIMITATION = "This is an estimated visible skin appearance under standardised lighting assumptions, not an exact biological melanin measurement."


def require_dependency(module_name: str):
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if os.getenv("REQUIRE_FASTAPI_TESTS") == "1":
            pytest.fail(f"Required dependency {module_name!r} is unavailable while REQUIRE_FASTAPI_TESTS=1")
        pytest.skip(f"Optional dependency {module_name!r} is unavailable in this environment")
        raise exc


@pytest.fixture
def client():
    require_dependency("fastapi")
    from fastapi.testclient import TestClient
    from app.api.router import create_fastapi_app

    return TestClient(create_fastapi_app())


def error_code(response):
    body = response.json()
    envelope = body.get("error") or body.get("detail", {}).get("error")
    return envelope["code"]


def register_and_login(client, email="user@example.com", roles=None):
    payload = {"email": email, "password": "CorrectHorseBatteryStaple123!"}
    if roles:
        payload["roles"] = roles
    client.post("/auth/register", json=payload)
    login = client.post(
        "/auth/login",
        json={"email": email, "password": payload["password"], "device_label": "pytest"},
    )
    data = login.json()
    return data["access_token"], data["refresh_token"], data["session_id"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def grant(client, token, purpose):
    return client.post("/consent", headers=auth_header(token), json={"purpose": purpose, "version": "2026-07"})


def complete_image(client, token, checksum="a" * 64, size=4096):
    payload = {"content_type": "image/png", "size_bytes": size, "checksum_sha256": checksum}
    request = client.post("/images/upload-request", headers=auth_header(token), json=payload)
    assert request.status_code == 200
    complete = client.post("/images/upload-complete", headers=auth_header(token), json=payload)
    assert complete.status_code == 200
    return complete.json()["image_id"]
