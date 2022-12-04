from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, joinedload, selectinload

from pfbudget.db.model import Bank, Category, Transaction

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

    class ClientSession:
        def __init__(self, engine):
            self.__engine = engine

        def __enter__(self):
            self.__session = Session(self.__engine)
            return self

        def __exit__(self, exc_type, exc_value, exc_tb):
            self.__session.close()

        def commit(self):
            self.__session.commit()

        def add(self, transactions: list[Transaction]):
            self.__session.add_all(transactions)

        def addcategory(self, category: Category):
            self.__session.add(category)

        def uncategorized(self) -> list[Transaction]:
            stmt = select(Transaction).where(~Transaction.category.has())
            return self.__session.scalars(stmt).all()

    def session(self):
        return self.ClientSession(self.engine)
