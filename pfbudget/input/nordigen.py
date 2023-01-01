from datetime import date
from time import sleep
from requests import HTTPError, ReadTimeout
from dotenv import load_dotenv
from nordigen import NordigenClient
from uuid import uuid4
import json
import os
import webbrowser

from .input import Input
from pfbudget.common.types import NoBankSelected
from pfbudget.db.model import Transaction
from pfbudget.utils import convert

load_dotenv()


class NordigenInput(Input):
    def __init__(self):
        super().__init__()
        self._client = NordigenClient(
            secret_key=os.environ.get("SECRET_KEY"),
            secret_id=os.environ.get("SECRET_ID"),
        )

        self.client.token = self.__token()

        # print(options)

        # if "all" in options and options["all"]:
        #     self.__banks = self.manager.get_banks()
        # elif "id" in options and options["id"]:
        #     self.__banks = [
        #         self.manager.get_bank_by("nordigen_id", b) for b in options["id"]
        #     ]
        # elif "name" in options and options["name"]:
        #     self.__banks = [
        #         self.manager.get_bank_by("name", b) for b in options["name"]
        #     ]
        # else:
        #     self.__banks = None

        self._start = date.min
        self._end = date.max

    def parse(self) -> list[Transaction]:
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
                    except ReadTimeout:
                        retries += 1
                        print(f"Request #{retries} timed-out, retrying in 1s")
                        sleep(1)
                    except HTTPError as e:
                        retries += 1
                        print(f"Request #{retries} failed with {e}, retrying in 1s")
                        sleep(1)

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

    def requisition(self, institution: str, country: str = "PT"):
        link, _ = self.__requisition_id(institution, country)
        webbrowser.open(link)

    def list(self, country: str):
        print(self._client.institution.get_institutions(country))

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
            return token

    def __requisition_id(self, i: str, c: str):
        id = self._client.institution.get_institution_id_by_name(
            country=c, institution=i
        )
        init = self._client.initialize_session(
            redirect_uri="https://murta.dev",
            institution_id=id,
            reference_id=str(uuid4()),
        )

        print(f"{i}({c}) link: {init.link} and requisition ID: {init.requisition_id}")
        return (init.link, init.requisition_id)
