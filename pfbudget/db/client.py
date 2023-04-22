from typing import Sequence

from pfbudget.db.model import Transaction


class Client:
    def __init__(self, url: str) -> None:
        self.url = url

    def insert(self, transactions: Sequence[Transaction]) -> None:
        raise NotImplementedError
