"""Weekly period

Revision ID: e77395969585
Revises: d18cbd50f7c6
Create Date: 2022-12-08 16:35:27.506504+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e77395969585"
down_revision = "d18cbd50f7c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE transactions.period ADD VALUE 'weekly' AFTER 'daily'")


def downgrade() -> None:
    op.execute(
        """CREATE TYPE transactions.period_new
        AS ENUM ('daily', 'monthly', 'yearly')
        """
    )
    op.execute("UPDATE transactions.categories_schedules SET period = DEFAULT WHERE period = 'weekly'")
    op.execute(
        """ALTER TABLE transactions.categories_schedules
        ALTER COLUMN period TYPE transactions.period_new
        USING period::text::transactions.period_new
        """
    )
    op.execute("DROP TYPE transactions.period")
    op.execute("ALTER TYPE transactions.period_new RENAME TO period")
