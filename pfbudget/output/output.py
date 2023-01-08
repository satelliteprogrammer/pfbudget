from abc import ABC, abstractmethod

from pfbudget.db.model import Transaction


class Output(ABC):
    @abstractmethod
    def report(self, transactions: list[Transaction]):
        raise NotImplementedError
