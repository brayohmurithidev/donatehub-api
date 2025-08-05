"""Campaign status

Revision ID: 9ef6e8a0b556
Revises: 59feaf1ac865
Create Date: 2025-08-04 18:40:11.689460

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ef6e8a0b556'
down_revision: Union[str, Sequence[str], None] = '59feaf1ac865'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create the ENUM type first
    campaign_status_enum = sa.Enum('active', 'completed', 'cancelled', name='campaignstatus')
    campaign_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add the new column using the enum
    op.add_column('campaigns', sa.Column('status', campaign_status_enum, nullable=True))


def downgrade() -> None:
    # 1. Drop the column first
    op.drop_column('campaigns', 'status')

    # 2. Then drop the enum type
    campaign_status_enum = sa.Enum('active', 'completed', 'cancelled', name='campaignstatus')
    campaign_status_enum.drop(op.get_bind(), checkfirst=True)
