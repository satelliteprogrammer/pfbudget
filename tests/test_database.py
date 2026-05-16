from datetime import date
from decimal import Decimal
import pytest

from mocks.client import MockClient

from pfbudget.db.client import Client
from pfbudget.db.model import (
    AccountType,
    Bank,
    NordigenBank,
    CategorySelector,
    CategoryRule,
    TagRule,
    Category,
    Tag,
    Transaction,
    TransactionCategory,
)


@pytest.fixture
def client() -> Client:
    return MockClient()


@pytest.fixture
def banks(client: Client) -> list[Bank]:
    banks = [
        Bank("bank", "BANK", AccountType.checking, NordigenBank(None, "req", None)),
        Bank("broker", "BROKER", AccountType.investment),
        Bank("creditcard", "CC", AccountType.MASTERCARD),
    ]

    # fix nordigen bank names which would be generated post DB insert
    for bank in banks:
        if bank.nordigen:
            bank.nordigen.name = bank.name

    client.insert(banks)
    return banks


@pytest.fixture
def transactions(client: Client) -> list[Transaction]:
    transactions = [
        Transaction(
            date(2023, 1, 1),
            "",
            Decimal("-10"),
            category=TransactionCategory("category", CategorySelector.algorithm),
        ),
        Transaction(date(2023, 1, 2), "", Decimal("-50")),
    ]

    client.insert(transactions)

    # fix ids which would be generated post DB insert
    for i, transaction in enumerate(transactions):
        transaction.id = i + 1
        if transaction.category:
            transaction.category.id = 1

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

    def test_update_bank_with_session(self, client: Client, banks: list[Bank]):
        with client.session as session:
            name = banks[0].name
            bank = session.select(Bank, lambda: Bank.name == name)[0]
            bank.name = "anotherbank"

        result = client.select(Bank, lambda: Bank.name == "anotherbank")
        assert len(result) == 1

    def test_update_bank(self, client: Client, banks: list[Bank]):
        name = banks[0].name

        result = client.select(Bank, lambda: Bank.name == name)
        assert result[0].type == AccountType.checking

        update = {"name": name, "type": AccountType.savings}
        client.update(Bank, [update])

        result = client.select(Bank, lambda: Bank.name == name)
        assert result[0].type == AccountType.savings

    def test_update_nordigen(self, client: Client, banks: list[Bank]):
        name = banks[0].name

        result = client.select(NordigenBank, lambda: NordigenBank.name == name)
        assert result[0].requisition_id == "req"

        update = {"name": name, "requisition_id": "anotherreq"}
        client.update(NordigenBank, [update])

        result = client.select(NordigenBank, lambda: NordigenBank.name == name)
        assert result[0].requisition_id == "anotherreq"

        result = client.select(Bank, lambda: Bank.name == name)
        assert getattr(result[0].nordigen, "requisition_id", None) == "anotherreq"

    def test_remove_bank(self, client: Client, banks: list[Bank]):
        name = banks[0].name

        result = client.select(Bank)
        assert len(result) == 3

        client.delete(Bank, Bank.name, [name])
        result = client.select(Bank)
        assert len(result) == 2

        names = [banks[1].name, banks[2].name]
        client.delete(Bank, Bank.name, names)
        result = client.select(Bank)
        assert len(result) == 0


def test_category_rule_construction_and_name_assignment():
    # Construct rule similarly to the CLI: keyword args then assign name
    rule = CategoryRule(
        start=date(2025, 4, 1),
        end=None,
        description="desc",
        regex="abc",
        bank=None,
        min=Decimal("-30"),
        max=None,
    )
    rule.name = "eating out"

    assert rule.start == date(2025, 4, 1)
    assert rule.description == "desc"
    assert rule.min == Decimal("-30")
    assert rule.name == "eating out"


def test_tag_rule_construction_and_tag_assignment():
    # Construct rule similarly to the CLI: keyword args then assign tag
    rule = TagRule(
        start=None,
        end=None,
        description=None,
        regex=None,
        bank=None,
        min=None,
        max=None,
    )
    rule.tag = "groceries"

    assert rule.start is None
    assert rule.tag == "groceries"


@pytest.fixture
def rules(client: Client) -> list:
    # create required Category and Tag
    cat = Category("eating out", None)
    tag = Tag("groceries")

    # create rules and associate with category/tag
    cr = CategoryRule(
        start=date(2025, 4, 1),
        end=None,
        description="desc",
        regex="abc",
        bank=None,
        min=Decimal("-30"),
        max=None,
    )
    cr.name = cat.name

    tr = TagRule(
        start=None,
        end=None,
        description=None,
        regex=None,
        bank=None,
        min=None,
        max=None,
    )
    tr.tag = tag.name

    # insert category, tag and rules
    client.insert([cat, tag, cr, tr])

    return [cr, tr]


def test_rules_insert_select_delete(client: Client, rules: list):
    # after fixture insertion, we should be able to select the rules
    cats = client.select(CategoryRule)
    tags = client.select(TagRule)

    assert any(r.name == "eating out" for r in cats)
    assert any(r.tag == "groceries" for r in tags)

    # delete the rules by id
    ids = [r.id for r in cats]
    if ids:
        client.delete(CategoryRule, CategoryRule.id, ids)

    assert client.select(CategoryRule) == []
