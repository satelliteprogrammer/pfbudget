import datetime as dt
import dotenv
import json
import nordigen
import os
import requests
import time
import uuid

import pfbudget.db.model as t
from pfbudget.utils.converters import convert

from .extract import Extract

dotenv.load_dotenv()


class PSD2Client(Extract):
    redirect_url = "https://murta.dev"

    def __init__(self):
        super().__init__()

        if not (key := os.environ.get("SECRET_KEY")) or not (
            id := os.environ.get("SECRET_ID")
        ):
            raise

        self._client = nordigen.NordigenClient(
            secret_key=key,
            secret_id=id,
        )

        self._client.token = self.__token()
        self._start = dt.date.min
        self._end = dt.date.max

    def parse(self) -> list[t.BankTransaction]:
        transactions = []
        assert len(self._banks) > 0

        for bank in self._banks:
            print(f"Downloading from {bank}...")
            requisition = self.client.requisition.get_requisition_by_id(
                bank.nordigen.requisition_id
            )

            print(requisition)
            for acc in requisition["accounts"]:
                account = self._client.account_api(acc)

                retries = 0
                downloaded = {}
                while retries < 3:
                    try:
                        downloaded = account.get_transactions()
                        break
                    except requests.ReadTimeout:
                        retries += 1
                        print(f"Request #{retries} timed-out, retrying in 1s")
                        time.sleep(1)
                    except requests.HTTPError as e:
                        retries += 1
                        print(f"Request #{retries} failed with {e}, retrying in 1s")
                        time.sleep(1)

                if not downloaded:
                    print(f"Couldn't download transactions for {account}")
                    continue

                with open("json/" + bank.name + ".json", "w") as f:
                    json.dump(downloaded, f)

                converted = [
                    convert(t, bank) for t in downloaded["transactions"]["booked"]
                ]

                transactions.extend(
                    [t for t in converted if self._start <= t.date <= self._end]
                )

        return sorted(transactions)

    def token(self):
        token = self._client.generate_token()
        print(f"New access token: {token}")
        return token

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
    def client(self):
        return self._client

    @property
    def banks(self):
        return self._banks

    @banks.setter
    def banks(self, value):
        self._banks = value

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

    def __token(self):
        if token := os.environ.get("TOKEN"):
            return token
        else:
            token = self._client.generate_token()
            print(f"New access token: {token}")
            return token["access"]
