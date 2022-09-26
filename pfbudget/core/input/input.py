from abc import ABC, abstractmethod

from pfbudget.core.transactions import Transactions


class Input(ABC):
    @abstractmethod
    def __init__(self, options: dict):
        self.options = options

    @abstractmethod
    def transactions(self) -> Transactions:
        return NotImplemented
