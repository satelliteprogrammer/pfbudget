from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, joinedload, selectinload

from pfbudget.db.model import Bank, Transaction

# import logging

# logging.basicConfig()
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


class DbClient:
    """
    General database client using sqlalchemy
    """

    __sessions: list[Session]

    def __init__(self, url: str) -> None:
        self._engine = create_engine(url)

    def get_transactions(self):
        """¿Non-optimized? get_transactions, will load the entire Transaction"""
        with Session(self.engine) as session:
            stmt = select(Transaction).options(
                joinedload("*"), selectinload(Transaction.tags)
            )
            return session.scalars(stmt).all()

    def get_uncategorized(self):
        with Session(self.engine) as session:
            stmt = select(Transaction).where(~Transaction.category.has())
            return session.scalars(stmt).all()

    def get_categorized(self):
        with Session(self.engine) as session:
            stmt = select(Transaction).where(Transaction.category.has())
            return session.scalars(stmt).all()

    def insert_transactions(self, input: list[Transaction]):
        with Session(self.engine) as session:
            session.add_all(input)
            session.commit()

    def get_banks(self):
        with Session(self.engine) as session:
            stmt = select(Bank)
            return session.scalars(stmt).all()

    def get_nordigen_banks(self):
        with Session(self.engine) as session:
            stmt = select(Bank).where(Bank.nordigen.has())
            return session.scalars(stmt).all()

    @property
    def engine(self):
        return self._engine
