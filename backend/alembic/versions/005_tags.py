"""Create tag and task_tag tables

Revision ID: 005_tags
Revises: 004_priority_enum
Create Date: 2026-02-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '005_tags'
down_revision: Union[str, None] = '004_priority_enum'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create tag table
    op.create_table(
        'tag',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Unique constraint: one tag name per user
    op.create_unique_constraint('uq_tag_user_name', 'tag', ['user_id', 'name'])
    op.create_index('ix_tag_user_id', 'tag', ['user_id'])

    # Create task_tag junction table
    op.create_table(
        'task_tag',
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('task.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tag.id', ondelete='CASCADE'), nullable=False),
        sa.PrimaryKeyConstraint('task_id', 'tag_id'),
    )

    op.create_index('ix_task_tag_tag_id', 'task_tag', ['tag_id'])


def downgrade() -> None:
    op.drop_index('ix_task_tag_tag_id', table_name='task_tag')
    op.drop_table('task_tag')
    op.drop_index('ix_tag_user_id', table_name='tag')
    op.drop_constraint('uq_tag_user_name', 'tag', type_='unique')
    op.drop_table('tag')
