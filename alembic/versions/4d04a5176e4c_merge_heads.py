"""merge heads

Revision ID: 4d04a5176e4c
Revises: 303c9d815b32, 7a1b2c3d4e55
Create Date: 2025-09-16 14:36:17.501824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d04a5176e4c'
down_revision: Union[str, Sequence[str], None] = ('303c9d815b32', '7a1b2c3d4e55')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
