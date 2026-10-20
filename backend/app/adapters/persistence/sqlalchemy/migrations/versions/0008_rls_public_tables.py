"""Close the Supabase Data API: RLS on every public table, no grants to its roles

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-20

Supabase exposes the public schema over PostgREST to the anon and authenticated roles,
and the publishable key ships in the frontend bundle, so every table was readable and
writable by anyone. The app never uses the Data API: the backend connects as the table
owner (postgres, BYPASSRLS), which RLS does not restrict.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = [
    "alembic_version",
    "campaign",
    "chunk",
    "citation",
    "conversation",
    "document",
    "embedding_space",
    "message",
    "system",
]

# anon/authenticated exist only on Supabase; plain Postgres (tests, local) skips this.
_REVOKE = """
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
    REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public
      REVOKE ALL ON TABLES FROM anon, authenticated;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public
      REVOKE ALL ON SEQUENCES FROM anon, authenticated;
  END IF;
END $$;
"""


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(_REVOKE)


def downgrade() -> None:
    # Grants are not restored: the Data API must never be reopened.
    for table in TABLES:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
