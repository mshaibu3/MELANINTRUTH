from app.api.phase3_app import ApiApplication
from app.api.router import create_fastapi_app
from app.db.models import NORMALIZED_TABLES


def test_create_fastapi_app_falls_back_or_mounts_required_contract():
    app = create_fastapi_app(ApiApplication())
    if hasattr(app, "openapi"):
        paths = app.openapi()["paths"]
    else:
        paths = app.openapi_contract()["paths"]
    for path in ["/auth/register", "/auth/login", "/consent", "/images/upload-request", "/analysis/jobs", "/renders", "/privacy/export", "/governance/model-versions", "/governance/audit"]:
        assert path in paths


def test_normalized_schema_specs_cover_required_tables():
    for table in ["users", "sessions", "consent_records", "image_captures", "analysis_jobs", "authentic_renders", "render_safety_reports", "audit_logs", "model_versions", "dataset_versions", "bias_reports", "incidents"]:
        assert table in NORMALIZED_TABLES
