from api_helpers import SCIENTIFIC_LIMITATION, require_dependency


def _client():
    require_dependency("fastapi")
    from fastapi.testclient import TestClient
    from app.api.router import create_fastapi_app

    return TestClient(create_fastapi_app())


def test_real_fastapi_health_openapi_and_headers():
    client = _client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    spec = client.get("/openapi.json").json()
    assert "/analysis/jobs" in spec["paths"]
    assert "Bearer" in str(spec) or "bearer" in str(spec)


def test_real_fastapi_auth_consent_image_analysis_render_flow():
    client = _client()
    assert client.get("/consent").status_code == 401
    reg = client.post(
        "/auth/register",
        json={"email": "fastapi@example.com", "password": "very-safe-password"},
    )
    assert reg.status_code == 200
    login = client.post(
        "/auth/login",
        json={"email": "fastapi@example.com", "password": "very-safe-password"},
    ).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    metadata = {
        "content_type": "image/jpeg",
        "size_bytes": 100,
        "checksum_sha256": "a" * 64,
    }
    denied = client.post(
        "/images/upload-request",
        headers=headers,
        json=metadata,
    )
    assert denied.status_code == 403
    client.post(
        "/consent",
        headers=headers,
        json={"purpose": "image_processing"},
    )
    client.post(
        "/consent",
        headers=headers,
        json={"purpose": "cloud_processing"},
    )
    ticket = client.post(
        "/images/upload-request",
        headers=headers,
        json=metadata,
    ).json()
    upload = client.post(
        "/images/upload-complete",
        headers=headers,
        json={
            **metadata,
            "upload_id": ticket["upload_id"],
            "idempotency_key": ticket["idempotency_key"],
        },
    ).json()
    analysis = client.post(
        "/analysis/jobs",
        headers=headers,
        json={
            "image_id": upload["image_id"],
            "pixels": [[(120, 105, 95), (130, 105, 95)] * 8 for _ in range(16)],
        },
    ).json()
    assert analysis["limitation_warning"] == SCIENTIFIC_LIMITATION
    render = client.post(
        "/renders",
        headers=headers,
        json={"analysis_id": analysis["id"], "confidence": 0.9},
    ).json()
    assert render["safety_gate_result"]["passed"]
