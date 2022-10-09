from abc import ABC, abstractmethod

from pfbudget.common.types import Transactions


class Input(ABC):
    @abstractmethod
    def __init__(self, options: dict):
        self.options = options

    @abstractmethod
    def parse(self) -> Transactions:
        return NotImplemented
