"""rename donations to campaign_donations

Revision ID: 7a1b2c3d4e55
Revises: ef2ff2ecc1ce
Create Date: 2025-09-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7a1b2c3d4e55'
down_revision: Union[str, Sequence[str], None] = 'ef2ff2ecc1ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename the donations table to campaign_donations to match the new ORM model
    op.rename_table('donations', 'campaign_donations')
    # Rename well-known constraints if they exist (PostgreSQL)
    try:
        op.execute("ALTER TABLE campaign_donations RENAME CONSTRAINT uq_donations_transaction_id TO uq_campaign_donations_transaction_id")
    except Exception:
        pass
    try:
        op.execute("ALTER TABLE campaign_donations RENAME CONSTRAINT fk_donations_tenant_id TO fk_campaign_donations_tenant_id")
    except Exception:
        pass
    try:
        op.execute("ALTER TABLE campaign_donations RENAME CONSTRAINT fk_donations_donor_id TO fk_campaign_donations_donor_id")
    except Exception:
        pass


def downgrade() -> None:
    # Revert the table name back to donations
    # First rename constraints back if present
    try:
        op.execute("ALTER TABLE campaign_donations RENAME CONSTRAINT uq_campaign_donations_transaction_id TO uq_donations_transaction_id")
    except Exception:
        pass
    try:
        op.execute("ALTER TABLE campaign_donations RENAME CONSTRAINT fk_campaign_donations_tenant_id TO fk_donations_tenant_id")
    except Exception:
        pass
    try:
        op.execute("ALTER TABLE campaign_donations RENAME CONSTRAINT fk_campaign_donations_donor_id TO fk_donations_donor_id")
    except Exception:
        pass
    op.rename_table('campaign_donations', 'donations')


