from abc import ABC, abstractmethod
from typing import Sequence

from pfbudget.db.model import Transaction


class Loader(ABC):
    @abstractmethod
    def load(self, transactions: Sequence[Transaction]) -> None:
        raise NotImplementedError
