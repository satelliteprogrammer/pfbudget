"""Drop SQLAlchemy enum

Revision ID: 60469d5dd2b0
Revises: b599dafcf468
Create Date: 2023-05-15 19:24:07.911352+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "60469d5dd2b0"
down_revision = "b599dafcf468"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TYPE pfbudget.scheduleperiod
        AS ENUM ('daily', 'weekly', 'monthly', 'yearly')
        """
    )
    op.execute(
        """ALTER TABLE pfbudget.category_schedules
        ALTER COLUMN period TYPE pfbudget.scheduleperiod
        USING period::text::pfbudget.scheduleperiod
        """
    )
    op.execute("DROP TYPE pfbudget.period")


def downgrade() -> None:
    op.execute(
        """
        CREATE TYPE pfbudget.period
        AS ENUM ('daily', 'weekly', 'monthly', 'yearly')
        """
    )
    op.execute(
        """ALTER TABLE pfbudget.category_schedules
        ALTER COLUMN period TYPE pfbudget.period
        USING period::text::pfbudget.period
        """
    )
    op.execute("DROP TYPE pfbudget.scheduleperiod")
