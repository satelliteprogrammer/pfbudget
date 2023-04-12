"""Add meal card

Revision ID: d3534f493239
Revises: 50ff1fbb8a00
Create Date: 2022-12-03 12:18:33.519666+00:00

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "d3534f493239"
down_revision = "50ff1fbb8a00"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE transactions.accounttype ADD VALUE 'mealcard' BEFORE 'VISA'")


def downgrade() -> None:
    op.execute(
        """CREATE TYPE transactions.accounttype_new
        AS ENUM ('checking', 'savings', 'investment', 'VISA', 'MASTERCARD')
        """
    )
    op.execute("UPDATE transactions.banks SET type = DEFAULT WHERE type = 'mealcard'")
    op.execute(
        """ALTER TABLE transactions.banks
        ALTER COLUMN type TYPE transactions.accounttype_new
        USING type::text::transactions.accounttype_new
        """
    )
    op.execute("DROP TYPE transactions.accounttype")
    op.execute("ALTER TYPE transactions.accounttype_new RENAME TO accounttype")
