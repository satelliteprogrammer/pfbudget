"""Selector type name change

Revision ID: b599dafcf468
Revises: 8623e709e111
Create Date: 2023-05-08 19:46:20.661214+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "b599dafcf468"
down_revision = "8623e709e111"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TYPE pfbudget.categoryselector
        AS ENUM ('unknown', 'nullifier', 'vacations', 'rules', 'algorithm', 'manual')
        """
    )
    op.execute(
        """ALTER TABLE pfbudget.transactions_categorized
        ALTER COLUMN selector TYPE pfbudget.categoryselector
        USING selector::text::pfbudget.categoryselector
        """
    )
    op.execute("DROP TYPE pfbudget.selector_t")


def downgrade() -> None:
    op.execute(
        """
        CREATE TYPE pfbudget.selector_t
        AS ENUM ('unknown', 'nullifier', 'vacations', 'rules', 'algorithm', 'manual')
        """
    )
    op.execute(
        """ALTER TABLE pfbudget.transactions_categorized
        ALTER COLUMN selector TYPE pfbudget.selector_t
        USING selector::text::pfbudget.selector_t
        """
    )
    op.execute("DROP TYPE pfbudget.categoryselector")
