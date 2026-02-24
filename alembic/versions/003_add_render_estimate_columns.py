"""Add render_factor and estimated_render_seconds columns to renders table.

Revision ID: 003
Revises: 002
Create Date: 2026-02-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "renders",
        sa.Column("render_factor", sa.Float(), nullable=True, server_default=sa.text("23.0")),
    )
    op.add_column(
        "renders",
        sa.Column("estimated_render_seconds", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("renders", "estimated_render_seconds")
    op.drop_column("renders", "render_factor")
