"""Completed action history and pipeline lifecycle support."""
from alembic import op
import sqlalchemy as sa

revision = "0005_pipeline"
down_revision = "0004_productivity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    if "crm_pursuitaction" not in sa.inspect(connection).get_table_names():
        op.create_table(
            "crm_pursuitaction",
            sa.Column("pursuit_id", sa.Uuid(), nullable=False),
            sa.Column("summary", sa.String(length=250), nullable=False),
            sa.Column("action_type", sa.String(length=40), nullable=False),
            sa.Column("due_date", sa.Date(), nullable=False),
            sa.Column("outcome", sa.String(length=80), nullable=False),
            sa.Column("note", sa.Text(), nullable=False, server_default=""),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_by_id", sa.BigInteger(), nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("tenant_id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by_id", sa.BigInteger(), nullable=True),
            sa.Column("updated_by_id", sa.BigInteger(), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.ForeignKeyConstraint(["completed_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["created_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["pursuit_id"], ["crm_pursuit.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["tenant_id"], ["crm_tenant.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_crm_pursuitaction_pursuit_id", "crm_pursuitaction", ["pursuit_id"])
        op.create_index("ix_crm_pursuitaction_tenant_id", "crm_pursuitaction", ["tenant_id"])
    if connection.dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS crm_pursuitaction_immutable ON crm_pursuitaction")
        op.execute("CREATE TRIGGER crm_pursuitaction_immutable BEFORE UPDATE OR DELETE ON crm_pursuitaction FOR EACH ROW EXECUTE FUNCTION atplcrm_prevent_history_mutation()")


def downgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS crm_pursuitaction_immutable ON crm_pursuitaction")
    op.drop_table("crm_pursuitaction")
