"""Add default timestamps to users

Revision ID: 7591e62d66c6
Revises: 25c5b7f1a9e2
Create Date: 2025-08-05 05:03:33.273817

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7591e62d66c6'
down_revision: Union[str, Sequence[str], None] = '25c5b7f1a9e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "users",
        "created_at",
        server_default=sa.text("now()"),
        existing_type=sa.TIMESTAMP(timezone=True),
    )
    op.alter_column(
        "users",
        "updated_at",
        server_default=sa.text("now()"),
        existing_type=sa.TIMESTAMP(timezone=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "users",
        "created_at",
        server_default=None,
        existing_type=sa.TIMESTAMP(timezone=True),
    )
    op.alter_column(
        "users",
        "updated_at",
        server_default=None,
        existing_type=sa.TIMESTAMP(timezone=True),
    )
