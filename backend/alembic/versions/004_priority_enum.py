"""Upgrade priority to P1-P4 enum

Revision ID: 004_priority_enum
Revises: 003_create_conversations
Create Date: 2026-02-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '004_priority_enum'
down_revision: Union[str, None] = '003_create_conversations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert existing free-text priorities to P1-P4
    op.execute("""
        UPDATE task SET priority = CASE
            WHEN priority = 'High'   THEN 'P2'
            WHEN priority = 'Medium' THEN 'P3'
            WHEN priority = 'Low'    THEN 'P4'
            ELSE 'P3'
        END
    """)

    # Alter column to VARCHAR(2) with default P3
    op.alter_column('task', 'priority',
                    type_=sa.String(2),
                    server_default='P3',
                    nullable=False)

    # Add check constraint
    op.create_check_constraint(
        'ck_task_priority',
        'task',
        "priority IN ('P1', 'P2', 'P3', 'P4')"
    )


def downgrade() -> None:
    # Drop check constraint
    op.drop_constraint('ck_task_priority', 'task', type_='check')

    # Convert P1-P4 back to free-text
    op.execute("""
        UPDATE task SET priority = CASE
            WHEN priority = 'P1' THEN 'High'
            WHEN priority = 'P2' THEN 'High'
            WHEN priority = 'P3' THEN 'Medium'
            WHEN priority = 'P4' THEN 'Low'
            ELSE 'Medium'
        END
    """)

    # Revert column type
    op.alter_column('task', 'priority',
                    type_=sa.String(),
                    server_default='Medium',
                    nullable=False)
