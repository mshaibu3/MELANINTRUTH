from __future__ import annotations

from api_helpers import SCIENTIFIC_LIMITATION, auth_header, complete_image, grant, register_and_login


def test_analysis_lifecycle_and_scoping(client):
    token, _, _ = register_and_login(client, email="analysis@example.com")
    grant(client, token, "image_processing")
    image_id = complete_image(client, token, checksum="f" * 64)
    missing_cloud = client.post("/analysis/jobs", headers=auth_header(token), json={"image_id": image_id, "cloud": True})
    assert missing_cloud.status_code == 403
    grant(client, token, "cloud_processing")
    low = client.post("/analysis/jobs", headers=auth_header(token), json={"image_id": image_id, "cloud": True, "sample_value": 0})
    assert low.status_code == 200
    assert low.json()["status"] in {"rejected_low_quality", "completed"}
    job = client.post("/analysis/jobs", headers=auth_header(token), json={"image_id": image_id, "cloud": True, "sample_value": 128})
    body = job.json()
    assert body["limitation_warning"] == SCIENTIFIC_LIMITATION
    for field in ["confidence_score", "uncertainty_score", "lighting_quality_score", "capture_quality_score", "retake_recommendation"]:
        assert field in body
    assert client.get("/analysis/jobs", headers=auth_header(token)).json()["jobs"]
    other_token, _, _ = register_and_login(client, email="analysis-other@example.com")
    assert client.get(f"/analysis/jobs/{body['id']}", headers=auth_header(other_token)).status_code == 404
