"""Commercial partner terms, fixed-rate governance and close evidence."""
from alembic import op
import sqlalchemy as sa

revision = "0007_commercial"
down_revision = "0006_notifications"
branch_labels = None
depends_on = None


def record_columns():
    return [
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
    ]


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    opportunity_columns = {item["name"] for item in inspector.get_columns("crm_opportunity")}
    for name, column in [
        ("probability_stage_default", sa.Column("probability_stage_default", sa.Integer(), nullable=False, server_default="20")),
        ("gross_margin_pct", sa.Column("gross_margin_pct", sa.Numeric(5, 2), nullable=True)),
        ("approval_note", sa.Column("approval_note", sa.Text(), nullable=False, server_default="")),
        ("close_notes", sa.Column("close_notes", sa.Text(), nullable=False, server_default="")),
        ("final_evidence_artifact_id", sa.Column("final_evidence_artifact_id", sa.Uuid(), nullable=True)),
    ]:
        if name not in opportunity_columns:
            op.add_column("crm_opportunity", column)
    inspector = sa.inspect(connection)
    if "crm_opportunity_final_evidence_fk" not in {item.get("name") for item in inspector.get_foreign_keys("crm_opportunity")}:
        op.create_foreign_key("crm_opportunity_final_evidence_fk", "crm_opportunity", "crm_artifact", ["final_evidence_artifact_id"], ["id"], ondelete="RESTRICT")
    op.execute("""
        UPDATE crm_opportunity AS opportunity
        SET probability_stage_default = COALESCE(
            (SELECT reference.numeric_value FROM crm_workspacereference AS reference
             WHERE reference.tenant_id = opportunity.tenant_id AND reference.category = 'stages'
               AND reference.code = opportunity.stage AND reference.is_deleted = false LIMIT 1),
            CASE opportunity.stage WHEN 'discovery' THEN 20 WHEN 'presales' THEN 35
              WHEN 'proposal' THEN 50 WHEN 'negotiation' THEN 70 WHEN 'contract' THEN 85
              WHEN 'won' THEN 100 ELSE 0 END)
    """)

    rate_columns = {item["name"] for item in inspector.get_columns("crm_exchangerate")}
    if "effective_date" not in rate_columns:
        op.add_column("crm_exchangerate", sa.Column("effective_date", sa.Date(), nullable=True))
    partner_columns = {item["name"] for item in inspector.get_columns("crm_partnerinvolvement")}
    for name, column in [
        ("applies_to", sa.Column("applies_to", sa.String(80), nullable=False, server_default="This contract only")),
        ("duration_months", sa.Column("duration_months", sa.Integer(), nullable=True)),
        ("agreement_artifact_id", sa.Column("agreement_artifact_id", sa.Uuid(), nullable=True)),
    ]:
        if name not in partner_columns:
            op.add_column("crm_partnerinvolvement", column)
    inspector = sa.inspect(connection)
    if "crm_partner_agreement_artifact_fk" not in {item.get("name") for item in inspector.get_foreign_keys("crm_partnerinvolvement")}:
        op.create_foreign_key("crm_partner_agreement_artifact_fk", "crm_partnerinvolvement", "crm_artifact", ["agreement_artifact_id"], ["id"], ondelete="RESTRICT")

    tables = set(inspector.get_table_names())
    if "crm_commercialsetting" not in tables:
        op.create_table(
            "crm_commercialsetting",
            sa.Column("partner_share_warning_pct", sa.Numeric(5, 2), nullable=False, server_default="40"),
            sa.Column("fx_movement_notice_pct", sa.Numeric(5, 2), nullable=False, server_default="5"),
            *record_columns(),
            sa.UniqueConstraint("tenant_id", name="crm_commercialsetting_tenant_uniq"),
        )
        op.create_index("ix_crm_commercialsetting_tenant_id", "crm_commercialsetting", ["tenant_id"])
    op.execute("""
        INSERT INTO crm_commercialsetting (id, tenant_id, created_at, updated_at, is_deleted, partner_share_warning_pct, fx_movement_notice_pct)
        SELECT gen_random_uuid(), id, now(), now(), false, 40, 5 FROM crm_tenant
        ON CONFLICT (tenant_id) DO NOTHING
    """)
    if "crm_exchangeratehistory" not in tables:
        op.create_table(
            "crm_exchangeratehistory",
            sa.Column("currency", sa.String(3), nullable=False),
            sa.Column("old_rate", sa.Numeric(18, 8), nullable=True),
            sa.Column("new_rate", sa.Numeric(18, 8), nullable=False),
            sa.Column("source", sa.String(100), nullable=False),
            sa.Column("effective_date", sa.Date(), nullable=True),
            sa.Column("change_type", sa.String(30), nullable=False, server_default="Manual override"),
            *record_columns(),
        )
        op.create_index("ix_crm_exchangeratehistory_currency", "crm_exchangeratehistory", ["currency"])
        op.create_index("ix_crm_exchangeratehistory_tenant_id", "crm_exchangeratehistory", ["tenant_id"])
    if connection.dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS crm_exchangeratehistory_immutable ON crm_exchangeratehistory")
        op.execute("CREATE TRIGGER crm_exchangeratehistory_immutable BEFORE UPDATE OR DELETE ON crm_exchangeratehistory FOR EACH ROW EXECUTE FUNCTION atplcrm_prevent_history_mutation()")


def downgrade() -> None:
    # Preserve commercial history, following the baseline's recovery-safe convention.
    pass
