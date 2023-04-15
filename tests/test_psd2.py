import datetime as dt
from decimal import Decimal
import pytest
import requests

import mocks.nordigen as mock

from pfbudget.db.model import Bank, BankTransaction, Nordigen
from pfbudget.extract.credentials import Credentials
from pfbudget.extract.exceptions import BankError, CredentialsError
from pfbudget.extract.psd2 import PSD2Client


class MockGet:
    def __init__(self, mock_exception=None):
        self._status_code = 200
        self._mock_exception = mock_exception

    def __call__(self, *args, **kwargs):
        if self._mock_exception:
            raise self._mock_exception

        self._headers = kwargs["headers"]
        if "Authorization" not in self._headers or not self._headers["Authorization"]:
            self._status_code = 401

        self.url = kwargs["url"]
        return self

    @property
    def ok(self):
        return True if self._status_code < 400 else False

    @property
    def status_code(self):
        return self._status_code

    def json(self):
        if self.url.endswith("accounts/" + mock.id + "/"):
            return mock.accounts_id
        elif self.url.endswith("accounts/" + mock.id + "/transactions/"):
            return mock.accounts_id_transactions
        elif self.url.endswith("requisitions/"):
            return mock.requisitions
        elif self.url.endswith("requisitions/" + mock.id + "/"):
            return mock.requisitions_id


@pytest.fixture(autouse=True)
def mock_requests(monkeypatch):
    monkeypatch.setattr("requests.get", MockGet())
    monkeypatch.delattr("requests.post")
    monkeypatch.delattr("requests.put")
    monkeypatch.delattr("requests.delete")


@pytest.fixture
def client() -> PSD2Client:
    credentials = Credentials("ID", "KEY", "TOKEN")
    return PSD2Client(credentials)


@pytest.fixture
def banks() -> list[Bank]:
    bank = Bank("Bank#1", "", "")
    bank.nordigen = Nordigen("", "", mock.id, False)
    return [bank]


class TestExtractPSD2:
    def test_empty_credentials(self):
        cred = Credentials("", "")
        with pytest.raises(CredentialsError):
            PSD2Client(cred)

    def test_empty_banks(self, client):
        with pytest.raises(BankError):
            client.extract([])

    def test_no_psd2_bank(self, client):
        with pytest.raises(BankError):
            client.extract([Bank("", "", "")])

    def test_timeout(self, monkeypatch, client, banks):
        monkeypatch.setattr(
            "requests.get", MockGet(mock_exception=requests.ReadTimeout)
        )
        with pytest.raises(requests.Timeout):
            client.extract(banks)

    def test_extract(self, client, banks):
        assert client.extract(banks) == [
            BankTransaction(
                dt.date(2023, 1, 14), "string", Decimal("328.18"), "Bank#1"
            ),
            BankTransaction(
                dt.date(2023, 2, 14), "string", Decimal("947.26"), "Bank#1"
            ),
        ]
