from copy import deepcopy
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from typing import Any, Optional, Sequence, Type, TypeVar

# from pfbudget.db.exceptions import InsertError, SelectError
from pfbudget.db.model import Transaction


class DatabaseSession:
    def __init__(self, session: Session):
        self.__session = session

    def __enter__(self):
        self.__session.begin()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        if exc_type:
            self.__session.rollback()
        else:
            self.__session.commit()
        self.__session.close()

    def insert(self, transactions: Sequence[Transaction]) -> None:
        self.__session.add_all(transactions)

    T = TypeVar("T")
    C = TypeVar("C")

    def select(self, what: Type[T], exists: Optional[Type[C]] = None) -> Sequence[T]:
        if exists:
            stmt = select(what).where(exists)
        else:
            stmt = select(what)

        return self.__session.scalars(stmt).all()


class Client:
    def __init__(self, url: str, **kwargs: Any):
        assert url, "Database URL is empty!"
        self._engine = create_engine(url, **kwargs)
        self._sessionmaker: Optional[sessionmaker[Session]] = None

    def insert(self, transactions: Sequence[Transaction]) -> None:
        new = deepcopy(transactions)
        with self.session as session:
            session.insert(new)

    T = TypeVar("T")
    C = TypeVar("C")

    def select(self, what: Type[T], exists: Optional[Type[C]] = None) -> Sequence[T]:
        return self.session.select(what, exists)

    @property
    def engine(self) -> Engine:
        return self._engine

    @property
    def session(self) -> DatabaseSession:
        if not self._sessionmaker:
            self._sessionmaker = sessionmaker(self._engine)

        return DatabaseSession(self._sessionmaker())
