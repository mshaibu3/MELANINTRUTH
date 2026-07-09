"""phase 3.8 required runtime table aliases

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

REQUIRED_TABLES = [
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


def upgrade():
    bind = op.get_bind()
    existing = set(inspect(bind).get_table_names())
    for table_name in REQUIRED_TABLES:
        if table_name in existing:
            continue
        op.create_table(
            table_name,
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=True),
            sa.Column("user_id", sa.String(36), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("payload", sa.JSON, nullable=False, server_default="{}"),
        )
        op.create_index(f"ix_{table_name}_tenant_user", table_name, ["tenant_id", "user_id"])
        op.create_index(f"ix_{table_name}_deleted_at", table_name, ["deleted_at"])


def downgrade():
    # Required runtime table names are owned by earlier schema migrations when already present.
    pass
