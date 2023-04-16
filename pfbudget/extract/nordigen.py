from dataclasses import dataclass
import dotenv
import json
import nordigen
import os
import requests
import time
import uuid

from .exceptions import CredentialsError, DownloadError

dotenv.load_dotenv()


@dataclass
class NordigenCredentials:
    id: str
    key: str
    token: str = ""

    def valid(self) -> bool:
        return self.id and self.key


class NordigenClient:
    redirect_url = "https://murta.dev"

    def __init__(self, credentials: NordigenCredentials):
        super().__init__()

        if not credentials.valid():
            raise CredentialsError

        self._client = nordigen.NordigenClient(
            secret_key=credentials.key, secret_id=credentials.id, timeout=5
        )

        if credentials.token:
            self._client.token = credentials.token

    def download(self, requisition_id):
        try:
            requisition = self._client.requisition.get_requisition_by_id(requisition_id)
            print(requisition)
        except requests.HTTPError as e:
            raise DownloadError(e)

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


class NordigenCredentialsManager:
    default = NordigenCredentials(
        os.environ.get("SECRET_ID"),
        os.environ.get("SECRET_KEY"),
        os.environ.get("TOKEN"),
    )
