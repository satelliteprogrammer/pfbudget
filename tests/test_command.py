from collections.abc import Sequence
import json
from pathlib import Path
import pytest
from typing import Any, cast

import mocks.transactions

from pfbudget.common.types import ExportFormat
from pfbudget.core.command import ExportCommand, ImportCommand
from pfbudget.db.client import Client
from pfbudget.db.model import Transaction


class FakeClient(Client):
    def __init__(self):
        self._transactions = mocks.transactions.simple

    def select(self, what: Any, *_) -> Sequence[Any]:
        if what == Transaction:
            return self.transactions
        return []

    def insert(self, *_):
        pass

    def update(self, *_):
        pass

    def delete(self, *_):
        pass

    @property
    def transactions(self):
        return self._transactions

    @transactions.setter
    def transactions(self, value: Sequence[Transaction]):
        self._transactions = value


@pytest.fixture
def client() -> Client:
    return FakeClient()


class TestCommand:
    def test_export_json(self, tmp_path: Path, client: Client):
        client = FakeClient()
        file = tmp_path / "test.json"
        command = ExportCommand(client, Transaction, file, ExportFormat.JSON)
        command.execute()

        with open(file, newline="") as f:
            result = json.load(f)
            assert result == [t.serialize() for t in mocks.transactions.simple]

        cast(FakeClient, client).transactions = mocks.transactions.simple_transformed
        command.execute()

        with open(file, newline="") as f:
            result = json.load(f)
            assert result == [
                t.serialize() for t in mocks.transactions.simple_transformed
            ]

    def test_export_pickle(self, tmp_path: Path, client: Client):
        file = tmp_path / "test.pickle"
        command = ExportCommand(client, Transaction, file, ExportFormat.pickle)
        with pytest.raises(AttributeError):
            command.execute()

    def test_import_json(self, tmp_path: Path, client: Client):
        file = tmp_path / "test"
        command = ExportCommand(client, Transaction, file, ExportFormat.JSON)
        command.execute()

        command = ImportCommand(client, Transaction, file, ExportFormat.JSON)
        command.execute()

        transactions = cast(FakeClient, client).transactions
        assert len(transactions) > 0
        assert transactions == client.select(Transaction)

    def test_import_pickle(self, tmp_path: Path, client: Client):
        file = tmp_path / "test"
        command = ExportCommand(client, Transaction, file, ExportFormat.pickle)
        with pytest.raises(AttributeError):
            command.execute()
