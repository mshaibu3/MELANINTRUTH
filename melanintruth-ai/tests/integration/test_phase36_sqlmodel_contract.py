from pathlib import Path

from app.db.models import NORMALIZED_TABLES, TABLE_SPECS


def test_core_orm_table_specs_are_postgres_ready():
    for name in ["users", "sessions", "devices", "tenants", "tenant_members", "consent_records", "image_captures", "analysis_jobs", "authentic_renders", "render_safety_reports", "audit_logs", "security_events", "data_export_requests", "data_deletion_requests", "model_versions", "dataset_versions", "bias_reports", "incidents"]:
        assert name in NORMALIZED_TABLES
        assert TABLE_SPECS[name].has_payload_json


def test_sqlmodel_repository_imports_without_optional_dependencies():
    from app.db.repositories.sqlmodel_runtime import SQLModelRepository

    assert SQLModelRepository is not None


def test_phase38_required_runtime_tables_are_declared_in_migration():
    migration = Path("melanintruth-ai/services/api/alembic/versions/0004_phase38_required_runtime_tables.py").read_text()
    required = [
        "users",
        "sessions",
        "devices",
        "tenants",
        "tenant_members",
        "consent_records",
        "image_captures",
        "image_quality_reports",
        "lighting_analyses",
        "skin_analyses",
        "analysis_jobs",
        "authentic_renders",
        "render_safety_reports",
        "audit_logs",
        "security_events",
        "data_export_requests",
        "data_deletion_requests",
        "model_versions",
        "dataset_versions",
        "bias_reports",
        "incidents",
    ]
    for table in required:
        assert f'"{table}"' in migration
