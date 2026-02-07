"""Convert due_date from VARCHAR to TIMESTAMPTZ

Revision ID: 007_due_date_type
Revises: 006_search_vector
Create Date: 2026-02-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '007_due_date_type'
down_revision: Union[str, None] = '006_search_vector'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert existing YYYY-MM-DD strings to TIMESTAMPTZ
    # First, alter column type using USING clause for data conversion
    op.execute("""
        ALTER TABLE task
        ALTER COLUMN due_date TYPE TIMESTAMPTZ
        USING CASE
            WHEN due_date IS NOT NULL AND due_date ~ '^\d{4}-\d{2}-\d{2}$'
            THEN (due_date || 'T00:00:00Z')::TIMESTAMPTZ
            WHEN due_date IS NOT NULL
            THEN due_date::TIMESTAMPTZ
            ELSE NULL
        END
    """)


def downgrade() -> None:
    # Convert TIMESTAMPTZ back to VARCHAR date strings
    op.execute("""
        ALTER TABLE task
        ALTER COLUMN due_date TYPE VARCHAR
        USING CASE
            WHEN due_date IS NOT NULL
            THEN to_char(due_date, 'YYYY-MM-DD')
            ELSE NULL
        END
    """)
