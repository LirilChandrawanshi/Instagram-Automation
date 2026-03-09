"""Add connected_at, paused_until, action_block_count for warm-up and block handling.

Revision ID: 002
Revises: 001
Create Date: 2026-03-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("instagram_accounts", sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("instagram_accounts", sa.Column("paused_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("instagram_accounts", sa.Column("action_block_count", sa.Integer(), nullable=False, server_default=sa.text("0")))


def downgrade() -> None:
    op.drop_column("instagram_accounts", "action_block_count")
    op.drop_column("instagram_accounts", "paused_until")
    op.drop_column("instagram_accounts", "connected_at")
