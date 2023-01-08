from dataclasses import asdict
from datetime import date
from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from pfbudget.db.model import (
    Category,
    CategoryGroup,
    CategoryRule,
    CategorySchedule,
    Link,
    Tag,
    TagRule,
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

        def expunge_all(self):
            self.__session.expunge_all()

        def get(self, type, column=None, values=None):
            if column:
                if values:
                    stmt = select(type).where(column.in_(values))
                else:
                    stmt = select(type).where(column.has())
            else:
                stmt = select(type)

            return self.__session.scalars(stmt).all()

        def add(self, rows: list):
            self.__session.add_all(rows)

        def remove_by_name(self, type: Category | Tag | Transaction, rows: list):
            stmt = delete(type).where(type.name.in_([row.name for row in rows]))
            self.__session.execute(stmt)

        def updategroup(self, categories: list[Category], group: CategoryGroup):
            stmt = (
                update(Category)
                .where(Category.name.in_([cat.name for cat in categories]))
                .values(group=group)
            )
            self.__session.execute(stmt)

        def updateschedules(self, schedules: list[CategorySchedule]):
            stmt = insert(CategorySchedule).values([asdict(s) for s in schedules])
            stmt = stmt.on_conflict_do_update(
                index_elements=[CategorySchedule.name],
                set_=dict(
                    recurring=stmt.excluded.recurring,
                    period=stmt.excluded.period,
                    period_multiplier=stmt.excluded.period_multiplier,
                ),
            )
            self.__session.execute(stmt)

        def remove_by_id(self, type: CategoryRule | TagRule, ids: list[int]):
            stmt = delete(type).where(type.id.in_(ids))
            self.__session.execute(stmt)

        def update(self, type, values: list[dict]):
            print(type, values)
            self.__session.execute(update(type), values)

        def remove_links(self, original, links: list):
            stmt = delete(Link).where(
                Link.original == original, Link.link.in_(link for link in links)
            )
            self.__session.execute(stmt)

        def transactions(self, min: date, max: date, banks: list[str]):
            stmt = select(Transaction).where(
                Transaction.date >= min,
                Transaction.date <= max,
                Transaction.bank.in_(banks),
            )
            return self.__session.scalars(stmt).all()

    def session(self) -> ClientSession:
        return self.ClientSession(self.engine)
