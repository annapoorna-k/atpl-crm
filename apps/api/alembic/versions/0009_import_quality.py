"""Excel imports and durable duplicate decisions."""
from alembic import op
import sqlalchemy as sa

revision = "0009_import_quality"
down_revision = "0008_relationship"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    import_columns = {item["name"] for item in inspector.get_columns("crm_importjob")}
    if "file_type" not in import_columns:
        op.add_column("crm_importjob", sa.Column("file_type", sa.String(10), nullable=False, server_default="csv"))
    if "warnings" not in import_columns:
        op.add_column("crm_importjob", sa.Column("warnings", sa.JSON(), nullable=False, server_default="[]"))
    if "crm_duplicatedecision" in inspector.get_table_names():
        return
    op.create_table(
        "crm_duplicatedecision",
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("first_id", sa.Uuid(), nullable=False),
        sa.Column("second_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(30), nullable=False, server_default="Distinct"),
        sa.Column("reason", sa.String(250), nullable=False, server_default=""),
        sa.Column("reviewed_by_id", sa.BigInteger(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_id", sa.BigInteger(), nullable=True),
        sa.Column("updated_by_id", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["created_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["crm_tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "entity_type", "first_id", "second_id", name="crm_duplicate_decision_pair_uniq"),
    )
    op.create_index("ix_crm_duplicatedecision_tenant_id", "crm_duplicatedecision", ["tenant_id"])
    op.create_index("ix_crm_duplicatedecision_entity_type", "crm_duplicatedecision", ["entity_type"])
    op.create_index("ix_crm_duplicatedecision_first_id", "crm_duplicatedecision", ["first_id"])
    op.create_index("ix_crm_duplicatedecision_second_id", "crm_duplicatedecision", ["second_id"])


def downgrade() -> None:
    # Preserve reviewed duplicate decisions during recovery.
    pass
