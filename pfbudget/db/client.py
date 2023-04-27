from copy import deepcopy
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from typing import Any, Optional, Sequence, Type, TypeVar

from pfbudget.db.exceptions import InsertError, SelectError
from pfbudget.db.model import Transaction


class Client:
    def __init__(self, url: str, **kwargs: dict[str, Any]) -> None:
        assert url, "Database URL is empty!"
        self._engine = create_engine(url, **kwargs)
        self._sessionmaker: Optional[sessionmaker[Session]] = None

    def insert(
        self, transactions: Sequence[Transaction], session: Optional[Session] = None
    ) -> None:
        if not session:
            new = deepcopy(transactions)
            with self.session as session_:
                try:
                    session_.add_all(new)
                except Exception as e:
                    session_.rollback()
                    raise InsertError(e)
                else:
                    session_.commit()
        else:
            try:
                session.add_all(transactions)
            except Exception as e:
                session.rollback()
                raise InsertError(e)
            else:
                session.commit()

    T = TypeVar("T")

    def select(self, what: Type[T], session: Optional[Session] = None) -> Sequence[T]:
        stmt = select(what)
        result: Sequence[what] = []

        if not session:
            with self.session as session_:
                try:
                    result = session_.scalars(stmt).all()
                except Exception as e:
                    session_.rollback()
                    raise SelectError(e)
        else:
            try:
                result = session.scalars(stmt).all()
            except Exception as e:
                session.rollback()
                raise SelectError(e)

        return result

    @property
    def engine(self) -> Engine:
        return self._engine

    @property
    def session(self) -> Session:
        if not self._sessionmaker:
            self._sessionmaker = sessionmaker(self._engine)
        return self._sessionmaker()
