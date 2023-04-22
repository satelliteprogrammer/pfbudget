from abc import ABC, abstractmethod
from typing import Sequence

from pfbudget.db.model import Transaction


class Transformer(ABC):
    @abstractmethod
    def transform(self, transactions: Sequence[Transaction]) -> Sequence[Transaction]:
        raise NotImplementedError

    @abstractmethod
    def transform_inplace(self, transactions: Sequence[Transaction]) -> None:
        raise NotImplementedError
