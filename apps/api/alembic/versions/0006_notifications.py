"""Notification preferences, delivery metadata and automation monitoring."""
from alembic import op
import sqlalchemy as sa

revision = "0006_notifications"
down_revision = "0005_pipeline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    notification_columns = {column["name"] for column in inspector.get_columns("crm_notification")}
    if "category" not in notification_columns:
        op.add_column("crm_notification", sa.Column("category", sa.String(length=40), nullable=False, server_default="general"))
        op.add_column("crm_notification", sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"))
        op.add_column("crm_notification", sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))
        op.create_index("ix_crm_notification_category", "crm_notification", ["category"])
    if "crm_notificationpreference" not in inspector.get_table_names():
        op.create_table(
            "crm_notificationpreference",
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            *[sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.true()) for name in (
                "due_actions", "stalled_pursuits", "blockers", "inactivity", "proposal_followup",
                "validation", "presales", "close_dates", "revisits", "system_failures", "weekly_summary",
            )],
            sa.Column("inactivity_days", sa.Integer(), nullable=False, server_default="21"),
            sa.Column("proposal_followup_days", sa.Integer(), nullable=False, server_default="7"),
            sa.Column("close_notice_days", sa.Integer(), nullable=False, server_default="7"),
            sa.Column("id", sa.Uuid(), nullable=False), sa.Column("tenant_id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by_id", sa.BigInteger(), nullable=True), sa.Column("updated_by_id", sa.BigInteger(), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.ForeignKeyConstraint(["user_id"], ["crm_user.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["tenant_id"], ["crm_tenant.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["created_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("tenant_id", "user_id", name="crm_notificationpreference_tenant_user_uniq"),
        )
        op.create_index("ix_crm_notificationpreference_tenant_id", "crm_notificationpreference", ["tenant_id"])
        op.create_index("ix_crm_notificationpreference_user_id", "crm_notificationpreference", ["user_id"])
    if "crm_automationrun" not in inspector.get_table_names():
        op.create_table(
            "crm_automationrun",
            sa.Column("task_name", sa.String(length=80), nullable=False), sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False), sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("detail", sa.Text(), nullable=False, server_default=""),
            sa.Column("id", sa.Uuid(), nullable=False), sa.Column("tenant_id", sa.Uuid(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_by_id", sa.BigInteger(), nullable=True), sa.Column("updated_by_id", sa.BigInteger(), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.ForeignKeyConstraint(["tenant_id"], ["crm_tenant.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["created_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_crm_automationrun_tenant_id", "crm_automationrun", ["tenant_id"])
        op.create_index("ix_crm_automationrun_task_name", "crm_automationrun", ["task_name"])
        op.create_index("ix_crm_automationrun_status", "crm_automationrun", ["status"])


def downgrade() -> None:
    op.drop_table("crm_automationrun")
    op.drop_table("crm_notificationpreference")
    op.drop_index("ix_crm_notification_category", table_name="crm_notification")
    op.drop_column("crm_notification", "read_at")
    op.drop_column("crm_notification", "severity")
    op.drop_column("crm_notification", "category")
