from copy import deepcopy
from dataclasses import asdict
from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, joinedload, selectinload

from pfbudget.db.model import (
    Bank,
    Category,
    CategoryGroup,
    CategoryRule,
    CategorySchedule,
    Transaction,
)

# import logging

# logging.basicConfig()
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)


class DbClient:
    """
    General database client using sqlalchemy
    """

    __sessions: list[Session]

    def __init__(self, url: str, echo=False) -> None:
        self._engine = create_engine(url, echo=echo)

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
            self.commit()
            self.__session.close()

        def commit(self):
            self.__session.commit()

        def add(self, transactions: list[Transaction]):
            self.__session.add_all(transactions)

        def addcategory(self, category: Category):
            self.__session.add(category)

        def removecategory(self, categories: list[Category]):
            stmt = delete(Category).where(
                Category.name.in_([cat.name for cat in categories])
            )
            self.__session.execute(stmt)

        def updategroup(self, categories: list[Category], group: CategoryGroup):
            stmt = (
                update(Category)
                .where(Category.name.in_([cat.name for cat in categories]))
                .values(group=group)
            )
            self.__session.execute(stmt)

        def updateschedules(
            self, categories: list[Category], schedule: CategorySchedule
        ):
            stmt = insert(CategorySchedule).values(
                [
                    dict(
                        name=cat.name,
                        recurring=schedule.recurring,
                        period=schedule.period,
                        period_multiplier=schedule.period_multiplier,
                    )
                    for cat in categories
                ]
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[CategorySchedule.name],
                set_=dict(
                    recurring=stmt.excluded.recurring,
                    period=stmt.excluded.period,
                    period_multiplier=stmt.excluded.period_multiplier,
                ),
            )
            self.__session.execute(stmt)

        def addrules(self, rules: list[CategoryRule]):
            self.__session.add_all(rules)

        def addcategorygroup(self, group: CategoryGroup):
            self.__session.add(group)

        def removecategorygroup(self, groups: list[CategoryGroup]):
            stmt = delete(CategoryGroup).where(
                CategoryGroup.name.in_([grp.name for grp in groups])
            )
            self.__session.execute(stmt)

        def uncategorized(self) -> list[Transaction]:
            stmt = select(Transaction).where(~Transaction.category.has())
            return self.__session.scalars(stmt).all()

    def session(self) -> ClientSession:
        return self.ClientSession(self.engine)
