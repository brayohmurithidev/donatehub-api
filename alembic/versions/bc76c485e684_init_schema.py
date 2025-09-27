"""init schema

Revision ID: bc76c485e684
Revises: 4d04a5176e4c
Create Date: 2025-09-27 00:27:51.834840

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'bc76c485e684'
down_revision: Union[str, Sequence[str], None] = '4d04a5176e4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define the enum separately
document_verification_status = sa.Enum(
    "PENDING", "APPROVED", "REJECTED",
    name="documentverificationstatus"
)


def upgrade() -> None:
    # Create the enum type first
    document_verification_status.create(op.get_bind(), checkfirst=True)

    # Add new columns
    op.add_column("tenants", sa.Column("is_email_verified", sa.Boolean(), nullable=True))
    op.add_column("tenants", sa.Column("document_verification_status", document_verification_status, nullable=False,
                                       server_default="PENDING"))
    op.add_column("tenants", sa.Column("document_verification_notes", sa.Text(), nullable=True))

    # Drop the old column
    op.drop_column("tenants", "is_Verified")

    # Drop old table and index
    op.drop_index(op.f("ix_mpesa_integrations_tenant_id"), table_name="mpesa_integrations")
    op.drop_table("mpesa_integrations")


def downgrade() -> None:
    # Recreate dropped column
    op.add_column("tenants", sa.Column("is_Verified", sa.Boolean(), nullable=True))

    # Remove new columns
    op.drop_column("tenants", "document_verification_notes")
    op.drop_column("tenants", "document_verification_status")
    op.drop_column("tenants", "is_email_verified")

    # Drop the enum type
    document_verification_status.drop(op.get_bind(), checkfirst=True)

    # Recreate mpesa_integrations table
    op.create_table(
        "mpesa_integrations",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.VARCHAR(), nullable=True),
        sa.Column("shortcode", sa.VARCHAR(), nullable=False),
        sa.Column("consumer_key", sa.VARCHAR(), nullable=False),
        sa.Column("consumer_secret", sa.VARCHAR(), nullable=False),
        sa.Column("passkey", sa.VARCHAR(), nullable=False),
        sa.Column("callback_url", sa.VARCHAR(), nullable=False),
        sa.Column("account_reference", sa.VARCHAR(), nullable=False),
        sa.Column("environment", sa.Enum("SANDBOX", "PRODUCTION", name="environmenttype"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
    )
    op.create_index(op.f("ix_mpesa_integrations_tenant_id"), "mpesa_integrations", ["tenant_id"], unique=False)
