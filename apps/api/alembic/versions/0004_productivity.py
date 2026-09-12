"""Personal saved views for productive CRM list workflows."""
from alembic import op
import sqlalchemy as sa

revision = "0004_productivity"
down_revision = "0003_data"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    if "crm_savedview" in sa.inspect(connection).get_table_names():
        return
    op.create_table(
        "crm_savedview",
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column("entity_type", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_id", sa.BigInteger(), nullable=True),
        sa.Column("updated_by_id", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["created_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_id"], ["crm_user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["crm_tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "owner_id", "entity_type", "name", name="crm_savedview_owner_entity_name_uniq"),
    )
    op.create_index("ix_crm_savedview_owner_id", "crm_savedview", ["owner_id"])
    op.create_index("ix_crm_savedview_tenant_id", "crm_savedview", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("crm_savedview")
