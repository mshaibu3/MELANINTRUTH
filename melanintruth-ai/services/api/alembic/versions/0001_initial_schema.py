"""initial production-shaped schema
Revision ID: 0001
Revises:
Create Date: 2026-07-07
"""
from alembic import op
import sqlalchemy as sa
revision="0001"; down_revision=None; branch_labels=None; depends_on=None
TABLES=["tenants","users","sessions","devices","roles","permissions","user_roles","consent_records","image_captures","image_quality_reports","lighting_analyses","skin_analyses","skin_regions","authentic_renders","render_safety_reports","progress_entries","recommendations","audit_logs","security_events","tenant_members","model_versions","dataset_versions","model_cards","dataset_cards","bias_reports","incidents","safety_reviews","data_export_requests","data_deletion_requests"]
def upgrade():
    for name in TABLES:
        op.create_table(name, sa.Column("id", sa.String(36), primary_key=True), sa.Column("tenant_id", sa.String(36), index=True, nullable=True), sa.Column("user_id", sa.String(36), index=True, nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.Column("deleted_at", sa.DateTime(timezone=True), index=True), sa.Column("payload", sa.JSON, nullable=False, server_default="{}"))
        op.create_index(f"ix_{name}_tenant_user", name, ["tenant_id","user_id"])
def downgrade():
    for name in reversed(TABLES): op.drop_table(name)
