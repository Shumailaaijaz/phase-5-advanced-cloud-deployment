"""Add reminder fields to task

Revision ID: 009_reminders
Revises: 008_recurrence
Create Date: 2026-02-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '009_reminders'
down_revision: Union[str, None] = '008_recurrence'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Minutes before due_date to send reminder
    op.add_column('task', sa.Column('reminder_minutes', sa.Integer(), nullable=True))

    # Whether reminder has been sent
    op.add_column('task', sa.Column('reminder_sent', sa.Boolean(), server_default='false', nullable=False))

    # Check constraint: reminder_minutes must be >= 0
    op.create_check_constraint(
        'ck_task_reminder_minutes',
        'task',
        'reminder_minutes IS NULL OR reminder_minutes >= 0'
    )

    # Partial index: unsent reminders with due dates (for efficient cron queries)
    op.execute("""
        CREATE INDEX ix_task_pending_reminders
        ON task (due_date, reminder_minutes)
        WHERE reminder_sent = false
          AND reminder_minutes IS NOT NULL
          AND due_date IS NOT NULL
          AND completed = false
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_task_pending_reminders")
    op.drop_constraint('ck_task_reminder_minutes', 'task', type_='check')
    op.drop_column('task', 'reminder_sent')
    op.drop_column('task', 'reminder_minutes')
