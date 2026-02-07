"""Add search_vector TSVECTOR column with GIN index

Revision ID: 006_search_vector
Revises: 005_tags
Create Date: 2026-02-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '006_search_vector'
down_revision: Union[str, None] = '005_tags'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add TSVECTOR column
    op.execute("ALTER TABLE task ADD COLUMN search_vector TSVECTOR")

    # Populate existing rows
    op.execute("""
        UPDATE task SET search_vector =
            to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, ''))
    """)

    # Create GIN index for fast full-text search
    op.execute("CREATE INDEX ix_task_search_vector ON task USING GIN (search_vector)")

    # Create trigger to auto-update search_vector on INSERT/UPDATE
    op.execute("""
        CREATE OR REPLACE FUNCTION task_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english', coalesce(NEW.title, '') || ' ' || coalesce(NEW.description, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    op.execute("""
        CREATE TRIGGER trg_task_search_vector
        BEFORE INSERT OR UPDATE OF title, description ON task
        FOR EACH ROW EXECUTE FUNCTION task_search_vector_update()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_task_search_vector ON task")
    op.execute("DROP FUNCTION IF EXISTS task_search_vector_update()")
    op.execute("DROP INDEX IF EXISTS ix_task_search_vector")
    op.execute("ALTER TABLE task DROP COLUMN IF EXISTS search_vector")
