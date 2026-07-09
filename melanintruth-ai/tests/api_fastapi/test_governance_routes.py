from __future__ import annotations

from api_helpers import auth_header, register_and_login


def test_governance_admin_controls(client):
    user_token, _, _ = register_and_login(client, email="gov-user@example.com")
    assert client.post("/governance/model-versions", headers=auth_header(user_token), json={}).status_code == 403
    admin_token, _, _ = register_and_login(client, email="gov-admin@example.com", roles=["admin"])
    missing_limitations = client.post("/governance/model-versions", headers=auth_header(admin_token), json={"model_id": "skin", "version": "1", "purpose": "analysis", "status": "candidate"})
    assert missing_limitations.status_code == 422
    production_missing_approval = client.post("/governance/model-versions", headers=auth_header(admin_token), json={"model_id": "skin", "version": "1", "purpose": "analysis", "status": "production", "known_limitations": "lighting dependent"})
    assert production_missing_approval.status_code == 422
    created = client.post("/governance/model-versions", headers=auth_header(admin_token), json={"model_id": "skin", "version": "1", "purpose": "analysis", "status": "production", "known_limitations": "lighting dependent", "approved_by": "review-board", "approval_date": "2026-07-08"})
    assert created.status_code == 200
    assert client.post("/governance/dataset-versions", headers=auth_header(admin_token), json={"version": "1"}).status_code == 422
    assert client.post("/governance/incidents", headers=auth_header(admin_token), json={"severity": "high"}).status_code == 422
    assert client.get("/governance/audit", headers=auth_header(admin_token)).status_code == 200
