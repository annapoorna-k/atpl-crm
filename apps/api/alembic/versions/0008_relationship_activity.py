"""Complete relationship records and contact activity tracking."""
from alembic import op
import sqlalchemy as sa

revision = "0008_relationship"
down_revision = "0007_commercial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    columns = {item["name"] for item in sa.inspect(connection).get_columns("crm_contact")}
    if "first_contacted_at" not in columns:
        op.add_column("crm_contact", sa.Column("first_contacted_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("""
        UPDATE crm_contact AS contact
        SET first_contacted_at = source.first_contacted_at
        FROM (
            SELECT contact_id, MIN(activity_date) AS first_contacted_at
            FROM crm_activity
            WHERE is_deleted = false AND is_client_facing = true AND direction = 'Outbound'
            GROUP BY contact_id
        ) AS source
        WHERE contact.id = source.contact_id AND contact.first_contacted_at IS NULL
    """)


def downgrade() -> None:
    # Keep relationship history during recovery, matching the existing migration policy.
    pass
