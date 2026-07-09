"""phase 3.5 normalized postgres-ready schema

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

TABLES = [
    "users", "sessions", "devices", "roles", "permissions", "user_roles", "consent_records", "image_captures", "image_quality_reports", "lighting_analyses", "skin_analyses", "analysis_jobs", "authentic_renders", "render_safety_reports", "progress_entries", "recommendations", "audit_logs", "security_events", "tenants", "tenant_members", "model_versions", "dataset_versions", "model_cards", "dataset_cards", "bias_reports", "incidents", "safety_reviews", "data_export_requests", "data_deletion_requests",
]


def upgrade():
    for table_name in TABLES:
        op.create_table(
            f"normalized_{table_name}",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=True, index=True),
            sa.Column("user_id", sa.String(36), nullable=True, index=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True, index=True),
            sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        )
        op.create_index(f"ix_normalized_{table_name}_tenant_user", f"normalized_{table_name}", ["tenant_id", "user_id"])
    op.create_index("ux_normalized_users_email", "normalized_users", [sa.text("(payload->>'email')")], unique=True, postgresql_using="btree")
    op.create_index("ix_normalized_sessions_refresh_hash", "normalized_sessions", [sa.text("(payload->>'refresh_token_hash')")], postgresql_using="btree")


def downgrade():
    for table_name in reversed(TABLES):
        op.drop_table(f"normalized_{table_name}")
