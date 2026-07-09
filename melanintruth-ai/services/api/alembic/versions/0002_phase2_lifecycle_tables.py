"""phase 2 lifecycle hardening fields

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-07
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "phase2_analysis_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("image_id", sa.String(36), nullable=False, index=True),
        sa.Column("status", sa.String(64), nullable=False, index=True),
        sa.Column("model_version", sa.String(128), nullable=False),
        sa.Column("quality_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("lighting_score", sa.Float, nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("uncertainty", sa.Float, nullable=False, server_default="1"),
        sa.Column("failure_reason", sa.Text),
        sa.Column("result", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), index=True),
    )
    op.create_table(
        "phase2_render_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("analysis_id", sa.String(36), nullable=False, index=True),
        sa.Column("status", sa.String(64), nullable=False, index=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="0"),
        sa.Column("uncertainty", sa.Float, nullable=False, server_default="1"),
        sa.Column("safety_report", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("rendered_ref", sa.String(512)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), index=True),
    )


def downgrade():
    op.drop_table("phase2_render_jobs")
    op.drop_table("phase2_analysis_jobs")
