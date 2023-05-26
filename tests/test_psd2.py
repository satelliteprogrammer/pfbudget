import datetime as dt
from decimal import Decimal
from typing import Any, Optional
import pytest
import requests

from mocks.client import MockClient
import mocks.nordigen as mock

from pfbudget.db.model import AccountType, Bank, BankTransaction, NordigenBank
from pfbudget.extract.exceptions import BankError, CredentialsError
from pfbudget.extract.extract import Extractor
from pfbudget.extract.nordigen import NordigenClient, NordigenCredentials
from pfbudget.extract.psd2 import PSD2Extractor


class MockGet:
    def __init__(self, mock_exception: Optional[Exception] = None):
        self._status_code = 200
        self._mock_exception = mock_exception

    def __call__(self, *args: Any, **kwargs: Any):
        if self._mock_exception:
            raise self._mock_exception

        self._headers: dict[str, str] = kwargs["headers"]
        if "Authorization" not in self._headers or not self._headers["Authorization"]:
            self._status_code = 401

        self.url: str = kwargs["url"]
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
def mock_requests(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("requests.get", MockGet())
    monkeypatch.delattr("requests.post")
    monkeypatch.delattr("requests.put")
    monkeypatch.delattr("requests.delete")


@pytest.fixture
def extractor() -> Extractor:
    credentials = NordigenCredentials("ID", "KEY")
    return PSD2Extractor(NordigenClient(credentials, MockClient()))


@pytest.fixture
def bank() -> Bank:
    bank = Bank("Bank#1", "", AccountType.checking, NordigenBank("", mock.id, False))
    return bank


class TestExtractPSD2:
    def test_empty_credentials(self):
        cred = NordigenCredentials("", "")
        with pytest.raises(CredentialsError):
            NordigenClient(cred, MockClient())

    def test_no_psd2_bank(self, extractor: Extractor):
        with pytest.raises(BankError):
            extractor.extract(Bank("", "", AccountType.checking))

    def test_timeout(
        self, monkeypatch: pytest.MonkeyPatch, extractor: Extractor, bank: Bank
    ):
        monkeypatch.setattr(
            "requests.get", MockGet(mock_exception=requests.ReadTimeout())
        )
        with pytest.raises(requests.Timeout):
            extractor.extract(bank)

    def test_extract(
        self, monkeypatch: pytest.MonkeyPatch, extractor: Extractor, bank: Bank
    ):
        monkeypatch.setattr(
            "pfbudget.extract.nordigen.NordigenClient.dump", lambda *args: None
        )
        assert extractor.extract(bank) == [
            BankTransaction(
                dt.date(2023, 1, 14), "string", Decimal("328.18"), bank="Bank#1"
            ),
            BankTransaction(
                dt.date(2023, 2, 14), "string", Decimal("947.26"), bank="Bank#1"
            ),
        ]
