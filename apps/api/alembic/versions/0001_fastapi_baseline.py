"""FastAPI/SQLAlchemy baseline preserving existing ATPLCRM data."""
from alembic import op
from sqlalchemy import text
from atplcrm.database import Base
from atplcrm import models  # noqa: F401

revision = "0001_fastapi"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    Base.metadata.create_all(connection)
    if connection.dialect.name == "postgresql":
        connection.execute(text("""CREATE OR REPLACE FUNCTION atplcrm_prevent_history_mutation()
            RETURNS trigger AS $$ BEGIN RAISE EXCEPTION 'ATPLCRM history is append-only'; END; $$ LANGUAGE plpgsql"""))
        for table in ("crm_auditevent", "crm_valuehistory"):
            connection.execute(text(f"DROP TRIGGER IF EXISTS {table}_immutable ON {table}"))
            connection.execute(text(f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION atplcrm_prevent_history_mutation()"))


def downgrade() -> None:
    pass
