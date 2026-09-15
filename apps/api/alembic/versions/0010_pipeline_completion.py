"""Tenant working calendar.

Revision ID: 0010_pipeline_completion
Revises: 0009_import_quality
"""
from alembic import op
import sqlalchemy as sa
revision = "0010_pipeline_completion"
down_revision = "0009_import_quality"
branch_labels = None
depends_on = None


def upgrade():
    if "crm_workingcalendar" in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        "crm_workingcalendar",
        sa.Column("working_weekdays", sa.JSON(), nullable=False, server_default="[0,1,2,3,4]"),
        sa.Column("holidays", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_id", sa.BigInteger(), nullable=True),
        sa.Column("updated_by_id", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["created_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["crm_tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", name="crm_workingcalendar_tenant_uniq"),
    )
    op.create_index("ix_crm_workingcalendar_tenant_id", "crm_workingcalendar", ["tenant_id"])


def downgrade():
    op.drop_index("ix_crm_workingcalendar_tenant_id", table_name="crm_workingcalendar")
    op.drop_table("crm_workingcalendar")
