from abc import ABC, abstractmethod
from typing import Sequence

from pfbudget.db.model import Transaction


class Transformer(ABC):
    @abstractmethod
    def transform(self, _: Sequence[Transaction]) -> Sequence[Transaction]:
        raise NotImplementedError
