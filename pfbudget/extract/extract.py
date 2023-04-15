from abc import ABC, abstractmethod

from pfbudget.db.model import Transaction


class Extract(ABC):
    @abstractmethod
    def extract(self) -> list[Transaction]:
        return NotImplementedError
