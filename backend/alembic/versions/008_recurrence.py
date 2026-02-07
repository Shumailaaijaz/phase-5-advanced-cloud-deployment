"""Add recurrence fields to task

Revision ID: 008_recurrence
Revises: 007_due_date_type
Create Date: 2026-02-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '008_recurrence'
down_revision: Union[str, None] = '007_due_date_type'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Recurrence rule: daily, weekly, monthly, or cron expression
    op.add_column('task', sa.Column('recurrence_rule', sa.String(100), nullable=True))

    # Parent task ID for recurrence chain
    op.add_column('task', sa.Column('recurrence_parent_id', sa.Integer(),
                                     sa.ForeignKey('task.id', ondelete='SET NULL'), nullable=True))

    # Depth counter to prevent infinite chains
    op.add_column('task', sa.Column('recurrence_depth', sa.Integer(), server_default='0', nullable=False))

    # Check constraint: depth must be 0-1000
    op.create_check_constraint(
        'ck_task_recurrence_depth',
        'task',
        'recurrence_depth >= 0 AND recurrence_depth <= 1000'
    )

    # Index on parent_id for chain lookups
    op.create_index('ix_task_recurrence_parent_id', 'task', ['recurrence_parent_id'])


def downgrade() -> None:
    op.drop_index('ix_task_recurrence_parent_id', table_name='task')
    op.drop_constraint('ck_task_recurrence_depth', 'task', type_='check')
    op.drop_column('task', 'recurrence_depth')
    op.drop_column('task', 'recurrence_parent_id')
    op.drop_column('task', 'recurrence_rule')
