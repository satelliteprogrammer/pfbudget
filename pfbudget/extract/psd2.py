import datetime as dt
import json
import nordigen
import requests
import time
import uuid

from typing import Sequence

import pfbudget.db.model as t
from pfbudget.utils.converters import convert

from .credentials import Credentials
from .exceptions import BankError, CredentialsError, ExtractError
from .extract import Extract


class PSD2Client(Extract):
    redirect_url = "https://murta.dev"

    def __init__(self, credentials: Credentials):
        super().__init__()

        if not credentials.valid():
            raise CredentialsError

        self._client = nordigen.NordigenClient(
            secret_key=credentials.key, secret_id=credentials.id, timeout=5
        )

        if credentials.token:
            self._client.token = credentials.token

        self._start = dt.date.min
        self._end = dt.date.max

    def extract(self, banks: Sequence[t.Bank]) -> list[t.BankTransaction]:
        transactions = []
        if not banks or any(not b.nordigen for b in banks):
            raise BankError

        for bank in banks:
            downloaded = None
            try:
                print(f"Downloading from {bank}...")
                downloaded = self.download(bank.nordigen.requisition_id)
            except requests.HTTPError as e:
                print(f"There was an issue downloading from {bank.name} -> {e}")
                raise ExtractError(e)

            if downloaded:
                self.dump(bank, downloaded)

                converted = [
                    convert(t, bank) for t in downloaded["transactions"]["booked"]
                ]

                transactions.extend(
                    [t for t in converted if self._start <= t.date <= self._end]
                )

        return sorted(transactions)

    def download(self, requisition_id):
        requisition = self._client.requisition.get_requisition_by_id(requisition_id)
        print(requisition)

        transactions = {}
        for acc in requisition["accounts"]:
            account = self._client.account_api(acc)

            retries = 0
            while retries < 3:
                try:
                    downloaded = account.get_transactions()
                    break
                except requests.ReadTimeout:
                    retries += 1
                    print(f"Request #{retries} timed-out, retrying in 1s")
                    time.sleep(1)

            if not downloaded:
                print(f"Couldn't download transactions for {account}")
                continue

            transactions.update(downloaded)

        return transactions

    def dump(self, bank, downloaded):
        with open("json/" + bank.name + ".json", "w") as f:
            json.dump(downloaded, f)

    def generate_token(self):
        self.token = self._client.generate_token()
        print(f"New access token: {self.token}")
        return self.token

    def requisition(self, id: str, country: str = "PT"):
        requisition = self._client.initialize_session(
            redirect_uri=self.redirect_url,
            institution_id=id,
            reference_id=str(uuid.uuid4()),
        )
        return requisition.link, requisition.requisition_id

    def country_banks(self, country: str):
        return self._client.institution.get_institutions(country)

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        self._start = value

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value):
        self._end = value

    # def __token(self):
    #     if token := os.environ.get("TOKEN"):
    #         return token
    #     else:
    #         token = self._client.generate_token()
    #         print(f"New access token: {token}")
    #         return token["access"]

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, value):
        if self._token:
            print("Replacing existing token with {value}")
        self._token = value
