from datetime import date
from decimal import Decimal
from typing import Sequence
import pytest

from pfbudget.db.client import Client
from pfbudget.db.model import BankTransaction, Transaction
from pfbudget.load.database import DatabaseLoader
from pfbudget.load.load import Loader


class FakeDatabaseClient(Client):
    def __init__(self, url: str) -> None:
        super().__init__(url)

    def insert(self, transactions: Sequence[Transaction]) -> None:
        pass


@pytest.fixture
def loader() -> Loader:
    url = "postgresql://user:pass@127.0.0.1:5432/db"
    client = FakeDatabaseClient(url)
    return DatabaseLoader(client)


class TestDatabaseLoad:
    def test_empty_url(self):
        with pytest.raises(AssertionError):
            _ = FakeDatabaseClient("")

    def test_insert(self, loader: Loader):
        transactions = [
            BankTransaction(date(2023, 1, 1), "", Decimal("-500"), bank="Bank#1"),
            BankTransaction(date(2023, 1, 2), "", Decimal("500"), bank="Bank#2"),
        ]

        loader.load(transactions)
