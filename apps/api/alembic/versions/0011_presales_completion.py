"""Complete pre-sales request lifecycle and capacity data.

Revision ID: 0011_presales_completion
Revises: 0010_pipeline_completion
"""
from alembic import op
import sqlalchemy as sa

revision = "0011_presales_completion"
down_revision = "0010_pipeline_completion"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_columns = {column["name"] for column in inspector.get_columns("crm_user")}
    if "weekly_capacity_days" not in user_columns:
        op.add_column("crm_user", sa.Column("weekly_capacity_days", sa.Numeric(5, 1), nullable=False, server_default="5"))

    request_columns = {column["name"] for column in inspector.get_columns("crm_presalesrequest")}
    additions = {
        "requested_by_id": sa.Column("requested_by_id", sa.BigInteger(), nullable=True),
        "deliverable_artifact_id": sa.Column("deliverable_artifact_id", sa.Uuid(), nullable=True),
        "review_note": sa.Column("review_note", sa.Text(), nullable=False, server_default=""),
        "approved_by_id": sa.Column("approved_by_id", sa.BigInteger(), nullable=True),
        "accepted_at": sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        "review_ready_at": sa.Column("review_ready_at", sa.DateTime(timezone=True), nullable=True),
        "approved_at": sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        "delivered_at": sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        "version": sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    }
    for name, column in additions.items():
        if name not in request_columns:
            op.add_column("crm_presalesrequest", column)
    op.execute("UPDATE crm_presalesrequest SET requested_by_id = created_by_id WHERE requested_by_id IS NULL")
    op.create_foreign_key("crm_presalesrequest_requested_by_fk", "crm_presalesrequest", "crm_user", ["requested_by_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("crm_presalesrequest_approved_by_fk", "crm_presalesrequest", "crm_user", ["approved_by_id"], ["id"], ondelete="RESTRICT")
    op.create_foreign_key("crm_presalesrequest_artifact_fk", "crm_presalesrequest", "crm_artifact", ["deliverable_artifact_id"], ["id"], ondelete="RESTRICT")
    op.alter_column("crm_presalesrequest", "assigned_to_id", existing_type=sa.BigInteger(), nullable=True)
    op.alter_column("crm_presalesrequest", "requested_by_id", existing_type=sa.BigInteger(), nullable=False)
    op.create_index("ix_crm_presalesrequest_requested_by_id", "crm_presalesrequest", ["requested_by_id"])
    op.create_index("ix_crm_presalesrequest_assigned_to_id", "crm_presalesrequest", ["assigned_to_id"])
    op.create_index("ix_crm_presalesrequest_status", "crm_presalesrequest", ["status"])
    op.create_index("ix_crm_presalesrequest_needed_by", "crm_presalesrequest", ["needed_by"])

    if "crm_presalescontributor" not in inspector.get_table_names():
        op.create_table(
            "crm_presalescontributor",
            sa.Column("request_id", sa.Uuid(), nullable=False),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("tenant_id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by_id", sa.BigInteger(), nullable=True),
            sa.Column("updated_by_id", sa.BigInteger(), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.ForeignKeyConstraint(["request_id"], ["crm_presalesrequest.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["crm_user.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["tenant_id"], ["crm_tenant.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["created_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("request_id", "user_id", name="crm_presalescontributor_request_user_uniq"),
        )
        op.create_index("ix_crm_presalescontributor_request_id", "crm_presalescontributor", ["request_id"])
        op.create_index("ix_crm_presalescontributor_user_id", "crm_presalescontributor", ["user_id"])
        op.create_index("ix_crm_presalescontributor_tenant_id", "crm_presalescontributor", ["tenant_id"])


def downgrade():
    op.drop_index("ix_crm_presalescontributor_tenant_id", table_name="crm_presalescontributor")
    op.drop_index("ix_crm_presalescontributor_user_id", table_name="crm_presalescontributor")
    op.drop_index("ix_crm_presalescontributor_request_id", table_name="crm_presalescontributor")
    op.drop_table("crm_presalescontributor")
    op.drop_index("ix_crm_presalesrequest_needed_by", table_name="crm_presalesrequest")
    op.drop_index("ix_crm_presalesrequest_status", table_name="crm_presalesrequest")
    op.drop_index("ix_crm_presalesrequest_assigned_to_id", table_name="crm_presalesrequest")
    op.drop_index("ix_crm_presalesrequest_requested_by_id", table_name="crm_presalesrequest")
    op.drop_constraint("crm_presalesrequest_artifact_fk", "crm_presalesrequest", type_="foreignkey")
    op.drop_constraint("crm_presalesrequest_approved_by_fk", "crm_presalesrequest", type_="foreignkey")
    op.drop_constraint("crm_presalesrequest_requested_by_fk", "crm_presalesrequest", type_="foreignkey")
    op.execute("UPDATE crm_presalesrequest SET assigned_to_id = requested_by_id WHERE assigned_to_id IS NULL")
    op.alter_column("crm_presalesrequest", "assigned_to_id", existing_type=sa.BigInteger(), nullable=False)
    for name in ("version", "delivered_at", "approved_at", "review_ready_at", "accepted_at", "approved_by_id", "review_note", "deliverable_artifact_id", "requested_by_id"):
        op.drop_column("crm_presalesrequest", name)
    op.drop_column("crm_user", "weekly_capacity_days")
