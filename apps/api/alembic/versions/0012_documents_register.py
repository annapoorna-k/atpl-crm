"""Complete documents, email linking and client-shared register.

Revision ID: 0012_documents_register
Revises: 0011_presales_completion
"""
from alembic import op
import sqlalchemy as sa

revision = "0012_documents_register"
down_revision = "0011_presales_completion"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    additions = {
        "company_id": sa.Column("company_id", sa.Uuid(), nullable=True),
        "storage_key": sa.Column("storage_key", sa.String(500), nullable=False, server_default=""),
        "original_filename": sa.Column("original_filename", sa.String(255), nullable=False, server_default=""),
        "content_type": sa.Column("content_type", sa.String(150), nullable=False, server_default=""),
        "byte_size": sa.Column("byte_size", sa.BigInteger(), nullable=False, server_default="0"),
        "checksum_sha256": sa.Column("checksum_sha256", sa.String(64), nullable=False, server_default=""),
        "supersedes_id": sa.Column("supersedes_id", sa.Uuid(), nullable=True),
        "source_artifact_id": sa.Column("source_artifact_id", sa.Uuid(), nullable=True),
        "parent_email_id": sa.Column("parent_email_id", sa.Uuid(), nullable=True),
        "email_classification": sa.Column("email_classification", sa.String(50), nullable=False, server_default=""),
        "message_reference": sa.Column("message_reference", sa.String(500), nullable=False, server_default=""),
        "email_subject": sa.Column("email_subject", sa.String(250), nullable=False, server_default=""),
        "email_date": sa.Column("email_date", sa.DateTime(timezone=True), nullable=True),
        "email_direction": sa.Column("email_direction", sa.String(20), nullable=False, server_default=""),
        "email_participants": sa.Column("email_participants", sa.JSON(), nullable=False, server_default="[]"),
        "is_reusable": sa.Column("is_reusable", sa.Boolean(), nullable=False, server_default=sa.false()),
        "approved_at": sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        "shared_with_client": sa.Column("shared_with_client", sa.Boolean(), nullable=False, server_default=sa.false()),
    }
    existing = {column["name"] for column in sa.inspect(bind).get_columns("crm_artifact")}
    for name, column in additions.items():
        if name not in existing: op.add_column("crm_artifact", column)
    op.execute("UPDATE crm_artifact AS a SET company_id = p.company_id FROM crm_pursuit AS p WHERE a.pursuit_id = p.id AND a.company_id IS NULL")
    op.alter_column("crm_artifact", "company_id", nullable=False)
    inspector = sa.inspect(bind)
    foreign_columns = {tuple(item.get("constrained_columns") or []) for item in inspector.get_foreign_keys("crm_artifact")}
    if ("company_id",) not in foreign_columns:
        op.create_foreign_key("crm_artifact_company_fk", "crm_artifact", "crm_company", ["company_id"], ["id"], ondelete="RESTRICT")
    for name, column in (("supersedes", "supersedes_id"), ("source", "source_artifact_id"), ("parent_email", "parent_email_id")):
        if (column,) not in foreign_columns:
            op.create_foreign_key(f"crm_artifact_{name}_fk", "crm_artifact", "crm_artifact", [column], ["id"], ondelete="RESTRICT")
    index_names = {item["name"] for item in sa.inspect(bind).get_indexes("crm_artifact")}
    for column in ("company_id", "supersedes_id", "parent_email_id", "is_reusable", "shared_with_client"):
        name = f"ix_crm_artifact_{column}"
        if name not in index_names:
            op.create_index(name, "crm_artifact", [column])
    if "crm_artifactrecipient" not in sa.inspect(bind).get_table_names():
        op.create_table(
        "crm_artifactrecipient",
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("contact_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_id", sa.BigInteger(), nullable=True),
        sa.Column("updated_by_id", sa.BigInteger(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["artifact_id"], ["crm_artifact.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["crm_contact.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["crm_tenant.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["crm_user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artifact_id", "contact_id", name="crm_artifactrecipient_artifact_contact_uniq"),
        )
        op.create_index("ix_crm_artifactrecipient_artifact_id", "crm_artifactrecipient", ["artifact_id"])
        op.create_index("ix_crm_artifactrecipient_contact_id", "crm_artifactrecipient", ["contact_id"])
        op.create_index("ix_crm_artifactrecipient_tenant_id", "crm_artifactrecipient", ["tenant_id"])


def downgrade():
    op.drop_table("crm_artifactrecipient")
    for column in ("shared_with_client", "is_reusable", "parent_email_id", "supersedes_id", "company_id"):
        op.drop_index(f"ix_crm_artifact_{column}", table_name="crm_artifact")
    for name in ("parent_email", "source", "supersedes", "company"):
        op.drop_constraint(f"crm_artifact_{name}_fk", "crm_artifact", type_="foreignkey")
    for name in ("shared_with_client", "approved_at", "is_reusable", "email_participants", "email_direction", "email_date", "email_subject", "message_reference", "email_classification", "parent_email_id", "source_artifact_id", "supersedes_id", "checksum_sha256", "byte_size", "content_type", "original_filename", "storage_key", "company_id"):
        op.drop_column("crm_artifact", name)
