from datetime import date
from decimal import Decimal
import pytest

from pfbudget.db.client import Client
from pfbudget.db.model import Base, Transaction


@pytest.fixture
def client() -> Client:
    url = "sqlite://"
    client = Client(url, execution_options={"schema_translate_map": {"pfbudget": None}})
    Base.metadata.create_all(client.engine)
    return client


class TestDatabase:
    def test_initialization(self, client: Client):
        pass

    def test_insert_transactions(self, client: Client):
        transactions = [
            Transaction(date(2023, 1, 1), "", Decimal("-500")),
            Transaction(date(2023, 1, 2), "", Decimal("500")),
        ]

        with client.session as session:
            client.insert(transactions, session)
            assert client.select(Transaction, session) == transactions

    def test_insert_transactions_independent_sessions(self, client: Client):
        transactions = [
            Transaction(date(2023, 1, 1), "", Decimal("-500")),
            Transaction(date(2023, 1, 2), "", Decimal("500")),
        ]

        client.insert(transactions)
        result = client.select(Transaction)
        for i, transaction in enumerate(result):
            assert transactions[i].date == transaction.date
            assert transactions[i].description == transaction.description
            assert transactions[i].amount == transaction.amount
