import json
from pathlib import Path
import pytest

from mocks.client import MockClient
import mocks.transactions

from pfbudget.common.types import ExportFormat
from pfbudget.core.command import ExportCommand, ImportCommand
from pfbudget.db.client import Client
from pfbudget.db.exceptions import InsertError
from pfbudget.db.model import Transaction


@pytest.fixture
def client() -> Client:
    return MockClient()


class TestCommand:
    def test_export_json(self, tmp_path: Path, client: Client):
        file = tmp_path / "test.json"
        client.insert(mocks.transactions.simple)

        command = ExportCommand(client, Transaction, file, ExportFormat.JSON)
        command.execute()

        with open(file, newline="") as f:
            result = json.load(f)
            assert result == [t.serialize() for t in client.select(Transaction)]

    def test_export_pickle(self, tmp_path: Path, client: Client):
        file = tmp_path / "test.pickle"
        command = ExportCommand(client, Transaction, file, ExportFormat.pickle)
        with pytest.raises(AttributeError):
            command.execute()

    def test_import_json(self, tmp_path: Path, client: Client):
        file = tmp_path / "test"
        client.insert(mocks.transactions.simple)

        command = ExportCommand(client, Transaction, file, ExportFormat.JSON)
        command.execute()

        # Since the transactions are already in the DB, we expect an insert error
        with pytest.raises(InsertError):
            command = ImportCommand(client, Transaction, file, ExportFormat.JSON)
            command.execute()

    def test_import_pickle(self, tmp_path: Path, client: Client):
        file = tmp_path / "test"
        command = ExportCommand(client, Transaction, file, ExportFormat.pickle)
        with pytest.raises(AttributeError):
            command.execute()
