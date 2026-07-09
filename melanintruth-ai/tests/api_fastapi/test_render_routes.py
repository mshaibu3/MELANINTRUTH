from __future__ import annotations

from api_helpers import SCIENTIFIC_LIMITATION, auth_header, complete_image, grant, register_and_login


def _completed_analysis(client, token):
    grant(client, token, "image_processing")
    grant(client, token, "cloud_processing")
    image_id = complete_image(client, token, checksum="1" * 64)
    return client.post("/analysis/jobs", headers=auth_header(token), json={"image_id": image_id, "cloud": True, "sample_value": 128}).json()["id"]


def test_render_safety_and_scoping(client):
    token, _, _ = register_and_login(client, email="render@example.com")
    not_found = client.post("/renders", headers=auth_header(token), json={"analysis_id": "missing"})
    assert not_found.status_code == 422
    analysis_id = _completed_analysis(client, token)
    unsafe = client.post("/renders", headers=auth_header(token), json={"analysis_id": analysis_id, "confidence": 0.1})
    assert unsafe.status_code == 200
    assert unsafe.json()["public_render_available"] is False
    safe = client.post("/renders", headers=auth_header(token), json={"analysis_id": analysis_id, "confidence": 0.95})
    body = safe.json()
    assert body["limitation_warning"] == SCIENTIFIC_LIMITATION
    assert body["safety_gate_result"]["passed"] is True
    assert body["public_render_available"] is True
    other_token, _, _ = register_and_login(client, email="render-other@example.com")
    assert client.get(f"/renders/{body['id']}", headers=auth_header(other_token)).status_code == 404
