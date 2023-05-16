from pathlib import Path
from typing import Any, Sequence, Type
import pytest

from mocks import banks, categories, transactions
from mocks.client import MockClient

from pfbudget.common.types import ExportFormat
from pfbudget.core.command import ExportCommand, ImportCommand, ImportFailedError
from pfbudget.db.client import Client
from pfbudget.db.model import (
    Bank,
    BankTransaction,
    Category,
    CategoryGroup,
    MoneyTransaction,
    Note,
    SplitTransaction,
    Tag,
    Transaction,
    TransactionCategory,
    TransactionTag,
)


@pytest.fixture
def client() -> Client:
    return MockClient()


params = [
    (transactions.simple, Transaction),
    (transactions.simple_transformed, Transaction),
    (transactions.bank, Transaction),
    (transactions.bank, BankTransaction),
    (transactions.money, Transaction),
    (transactions.money, MoneyTransaction),
    (transactions.split, SplitTransaction),
    ([banks.checking, banks.cc], Bank),
    ([categories.category_null, categories.category1, categories.category2], Category),
    (
        [
            categories.categorygroup1,
            categories.category_null,
            categories.category1,
            categories.category2,
        ],
        CategoryGroup,
    ),
    ([categories.tag_1], Tag),
]

not_serializable = [
    (transactions.simple_transformed, TransactionCategory),
    (transactions.tagged, TransactionTag),
    (transactions.noted, Note),
]


class TestBackup:
    @pytest.mark.parametrize("input, what", params)
    def test_import(self, tmp_path: Path, input: Sequence[Any], what: Type[Any]):
        file = tmp_path / "test.json"

        client = MockClient()
        client.insert(input)
        originals = client.select(what)

        assert originals

        command = ExportCommand(client, what, file, ExportFormat.JSON)
        command.execute()

        other = MockClient()
        command = ImportCommand(other, what, file, ExportFormat.JSON)
        command.execute()

        imported = other.select(what)

        assert originals == imported

    @pytest.mark.parametrize("input, what", not_serializable)
    def test_try_backup_not_serializable(
        self, tmp_path: Path, input: Sequence[Any], what: Type[Any]
    ):
        file = tmp_path / "test.json"

        client = MockClient()
        client.insert(input)
        originals = client.select(what)
        assert originals

        command = ExportCommand(client, what, file, ExportFormat.JSON)

        with pytest.raises(AttributeError):
            command.execute()

        other = MockClient()
        command = ImportCommand(other, what, file, ExportFormat.JSON)

        with pytest.raises(ImportFailedError):
            command.execute()

        imported = other.select(what)
        assert not imported
