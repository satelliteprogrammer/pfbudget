from abc import ABC, abstractmethod
from datetime import date
from typing import Sequence

from pfbudget.db.model import Bank, Transaction


class Extractor(ABC):
    @abstractmethod
    def extract(
        self, bank: Bank, start: date = date.min, end: date = date.max
    ) -> Sequence[Transaction]:
        raise NotImplementedError
