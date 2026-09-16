"""Local demo readiness: login throttling, recent search and search indexes.

Revision ID: 0013_demo_readiness
Revises: 0012_documents_register
"""
from alembic import op
import sqlalchemy as sa

revision = "0013_demo_readiness"
down_revision = "0012_documents_register"
branch_labels = None
depends_on = None


def record_columns():
    return (
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_id", sa.BigInteger(), nullable=True),
        sa.Column("updated_by_id", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
    )


def create_index_if_missing(inspector, name: str, table: str, columns: list[str]) -> None:
    if name not in {item["name"] for item in inspector.get_indexes(table)}:
        op.create_index(name, table, columns)


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "app_loginthrottle" not in tables:
        op.create_table(
            "app_loginthrottle",
            sa.Column("key_hash", sa.String(64), primary_key=True),
            sa.Column("failures", sa.Integer(), nullable=False),
            sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True),
        )
    inspector = sa.inspect(bind)
    create_index_if_missing(inspector, "ix_app_loginthrottle_blocked_until", "app_loginthrottle", ["blocked_until"])

    if "crm_searchhistory" not in tables:
        op.create_table(
            "crm_searchhistory",
            *record_columns(),
            sa.Column("user_id", sa.BigInteger(), nullable=False),
            sa.Column("query", sa.String(120), nullable=False),
            sa.Column("entity_type", sa.String(30), nullable=False),
            sa.Column("filters", sa.JSON(), nullable=False),
            sa.Column("signature", sa.String(64), nullable=False),
            sa.Column("use_count", sa.Integer(), nullable=False),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["tenant_id"], ["crm_tenant.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["user_id"], ["crm_user.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["updated_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("tenant_id", "user_id", "signature", name="crm_searchhistory_user_signature_uniq"),
        )

    inspector = sa.inspect(bind)
    for name, table, columns in (
        ("ix_crm_searchhistory_tenant_id", "crm_searchhistory", ["tenant_id"]),
        ("ix_crm_searchhistory_user_id", "crm_searchhistory", ["user_id"]),
        ("ix_crm_searchhistory_last_used_at", "crm_searchhistory", ["last_used_at"]),
        ("ix_crm_company_owner_country", "crm_company", ["tenant_id", "owner_id", "country"]),
        ("ix_crm_contact_owner_country", "crm_contact", ["tenant_id", "owner_id", "country"]),
        ("ix_crm_pursuit_owner_holder_action", "crm_pursuit", ["tenant_id", "owner_id", "holder_id", "action_date"]),
        ("ix_crm_pursuit_source", "crm_pursuit", ["tenant_id", "source_channel"]),
        ("ix_crm_opportunity_stage_close", "crm_opportunity", ["tenant_id", "stage", "expected_close_date"]),
        ("ix_crm_opportunity_service", "crm_opportunity", ["tenant_id", "service_line"]),
    ):
        create_index_if_missing(inspector, name, table, columns)

    if bind.dialect.name == "postgresql":
        for table, expression in (
            ("crm_company", "coalesce(name,'') || ' ' || coalesce(domain,'') || ' ' || coalesce(industry,'') || ' ' || coalesce(country,'')"),
            ("crm_contact", "coalesce(first_name,'') || ' ' || coalesce(last_name,'') || ' ' || coalesce(email,'') || ' ' || coalesce(phone,'') || ' ' || coalesce(mobile,'')"),
            ("crm_pursuit", "coalesce(name,'') || ' ' || coalesce(source_detail,'') || ' ' || coalesce(source_channel,'')"),
        ):
            if "search_vector" not in {column["name"] for column in sa.inspect(bind).get_columns(table)}:
                op.execute(f"ALTER TABLE {table} ADD COLUMN search_vector tsvector GENERATED ALWAYS AS (to_tsvector('simple', {expression})) STORED")
            name = f"ix_{table}_search_fts"
            if name not in {item["name"] for item in sa.inspect(bind).get_indexes(table)}:
                op.execute(f"CREATE INDEX {name} ON {table} USING gin (search_vector)")


def downgrade():
    if op.get_bind().dialect.name == "postgresql":
        for name in ("ix_crm_pursuit_search_fts", "ix_crm_contact_search_fts", "ix_crm_company_search_fts"):
            op.execute(f"DROP INDEX IF EXISTS {name}")
        for table in ("crm_pursuit", "crm_contact", "crm_company"):
            op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS search_vector")
    for name, table in (
        ("ix_crm_opportunity_service", "crm_opportunity"), ("ix_crm_opportunity_stage_close", "crm_opportunity"),
        ("ix_crm_pursuit_source", "crm_pursuit"), ("ix_crm_pursuit_owner_holder_action", "crm_pursuit"),
        ("ix_crm_contact_owner_country", "crm_contact"), ("ix_crm_company_owner_country", "crm_company"),
    ):
        op.drop_index(name, table_name=table)
    op.drop_table("crm_searchhistory")
    op.drop_table("app_loginthrottle")
