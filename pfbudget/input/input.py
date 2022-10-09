from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pfbudget.common.types import Transactions

if TYPE_CHECKING:
    from pfbudget.core.manager import Manager


class Input(ABC):
    def __init__(self, manager: Manager):
        self._manager = manager

    @abstractmethod
    def parse(self) -> Transactions:
        return NotImplemented

    @property
    def manager(self):
        return self._manager
