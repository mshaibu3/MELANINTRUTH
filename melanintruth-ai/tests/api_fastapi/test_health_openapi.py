from __future__ import annotations


def test_health_openapi_and_schemas(client):
    assert client.get("/health").json()["status"] == "ok"
    spec = client.get("/openapi.json").json()
    for path in ["/auth/register", "/images/upload-request", "/analysis/jobs", "/renders", "/privacy/export", "/governance/model-versions"]:
        assert path in spec["paths"]
    assert "HTTPBearer" in spec["components"]["securitySchemes"] or "BearerAuth" in spec["components"]["securitySchemes"]
    assert "ErrorEnvelope" in spec["components"].get("schemas", {})
