from datetime import date
from decimal import Decimal
import pytest

from pfbudget.db.client import Client
from pfbudget.db.model import (
    AccountType,
    Bank,
    Base,
    CategorySelector,
    Nordigen,
    Selector_T,
    Transaction,
    TransactionCategory,
)


@pytest.fixture
def client() -> Client:
    url = "sqlite://"
    client = Client(url, execution_options={"schema_translate_map": {"pfbudget": None}})
    Base.metadata.create_all(client.engine)
    return client


@pytest.fixture
def banks(client: Client) -> list[Bank]:
    banks = [
        Bank("bank", "BANK", AccountType.checking),
        Bank("broker", "BROKER", AccountType.investment),
        Bank("creditcard", "CC", AccountType.MASTERCARD),
    ]
    banks[0].nordigen = Nordigen("bank", None, "req", None)

    client.insert(banks)
    return banks


@pytest.fixture
def transactions(client: Client) -> list[Transaction]:
    transactions = [
        Transaction(date(2023, 1, 1), "", Decimal("-10")),
        Transaction(date(2023, 1, 2), "", Decimal("-50")),
    ]
    transactions[0].category = TransactionCategory(
        "name", CategorySelector(Selector_T.algorithm)
    )

    client.insert(transactions)
    for i, transaction in enumerate(transactions):
        transaction.id = i + 1
        transaction.split = False  # default
    transactions[0].category.id = 1
    transactions[0].category.selector.id = 1

    return transactions


class TestDatabase:
    def test_initialization(self, client: Client):
        pass

    def test_insert_with_session(self, client: Client):
        transactions = [
            Transaction(date(2023, 1, 1), "", Decimal("-10")),
            Transaction(date(2023, 1, 2), "", Decimal("-50")),
        ]

        with client.session as session:
            session.insert(transactions)
            assert session.select(Transaction) == transactions

    def test_insert_transactions(self, client: Client, transactions: list[Transaction]):
        result = client.select(Transaction)
        assert result == transactions

    def test_select_transactions_without_category(
        self, client: Client, transactions: list[Transaction]
    ):
        result = client.select(Transaction, lambda: ~Transaction.category.has())
        assert result == [transactions[1]]

    def test_select_banks(self, client: Client, banks: list[Bank]):
        result = client.select(Bank)
        assert result == banks

    def test_select_banks_with_nordigen(self, client: Client, banks: list[Bank]):
        result = client.select(Bank, Bank.nordigen)
        assert result == [banks[0]]

    def test_select_banks_by_name(self, client: Client, banks: list[Bank]):
        name = banks[0].name
        result = client.select(Bank, lambda: Bank.name == name)
        assert result == [banks[0]]

        names = [banks[0].name, banks[1].name]
        result = client.select(Bank, lambda: Bank.name.in_(names))
        assert result == [banks[0], banks[1]]
