from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = 'dc3df10c3c59'
down_revision: Union[str, Sequence[str], None] = 'c1040f53e626'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Re-create the lowercase enum
new_enum = sa.Enum('sandbox', 'production', name='environmenttype')


def upgrade() -> None:
    # Create the new enum type
    new_enum.create(op.get_bind(), checkfirst=True)

    # Alter the column to use the new enum (PostgreSQL only)
    op.execute("""
        ALTER TABLE mpesa_integrations
        ALTER COLUMN environment
        TYPE environmenttype
        USING environment::text::environmenttype
    """)


def downgrade() -> None:
    # Optional: drop the lowercase enum
    op.execute("""
        ALTER TABLE mpesa_integrations
        ALTER COLUMN environment
        TYPE TEXT
    """)
    op.execute("DROP TYPE IF EXISTS environmenttype")