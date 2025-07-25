"""Category selector

Revision ID: 6863dda76ea2
Revises: 83f4c9837f6e
Create Date: 2022-12-08 00:56:59.032641+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6863dda76ea2"
down_revision = "83f4c9837f6e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "categories_selector",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column(
            "selector",
            sa.Enum(
                "unknown",
                "nullifier",
                "vacations",
                "rules",
                "algorithm",
                "manual",
                name="selector",
                schema="transactions",
                inherit_schema=True,
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["id"],
            ["transactions.categorized.id"],
            name=op.f("fk_categories_selector_id_categorized"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories_selector")),
        schema="transactions",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("categories_selector", schema="transactions")
    # ### end Alembic commands ###
