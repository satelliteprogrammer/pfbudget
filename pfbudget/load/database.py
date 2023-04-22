from typing import Sequence

from pfbudget.db.client import Client
from pfbudget.db.model import Transaction

from .load import Loader


class DatabaseLoader(Loader):
    def __init__(self, client: Client) -> None:
        self.client = client

    def load(self, transactions: Sequence[Transaction]) -> None:
        self.client.insert(transactions)
