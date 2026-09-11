"""Workspace administration and configurable reference data."""
from alembic import op
import sqlalchemy as sa
revision = "0002_admin"
down_revision = "0001_fastapi"
branch_labels = None
depends_on = None

def upgrade() -> None:
    connection = op.get_bind()
    if "crm_workspacereference" in sa.inspect(connection).get_table_names(): return
    op.create_table("crm_workspacereference", sa.Column("category", sa.String(length=40), nullable=False), sa.Column("code", sa.String(length=80), nullable=False), sa.Column("label", sa.String(length=120), nullable=False), sa.Column("numeric_value", sa.Integer(), nullable=True), sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("id", sa.Uuid(), nullable=False), sa.Column("tenant_id", sa.Uuid(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_by_id", sa.BigInteger(), nullable=True), sa.Column("updated_by_id", sa.BigInteger(), nullable=True), sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()), sa.ForeignKeyConstraint(["created_by_id"], ["crm_user.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["tenant_id"], ["crm_tenant.id"], ondelete="RESTRICT"), sa.ForeignKeyConstraint(["updated_by_id"], ["crm_user.id"], ondelete="RESTRICT"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("tenant_id", "category", "code", name="crm_reference_tenant_category_code_uniq"))
    op.create_index("ix_crm_workspacereference_category", "crm_workspacereference", ["category"]); op.create_index("ix_crm_workspacereference_tenant_id", "crm_workspacereference", ["tenant_id"])

def downgrade() -> None: op.drop_table("crm_workspacereference")
