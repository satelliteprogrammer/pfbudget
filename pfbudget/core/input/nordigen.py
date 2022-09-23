from dotenv import load_dotenv
from json import dump
from nordigen import NordigenClient
from uuid import uuid4
import os
import webbrowser

load_dotenv()


class Client:
    def __init__(self):
        self._client = NordigenClient(
            secret_key=os.environ.get("SECRET_KEY"),
            secret_id=os.environ.get("SECRET_ID"),
        )

        self._client.token = self.__token()

    def token(self):
        token = self._client.generate_token()
        print(f"New access token: {token}")
        return token

    def requisition(self, institution: str, country: str = "PT"):
        link, _ = self.__requisition_id(institution, country)
        webbrowser.open(link)

    def download(self, id: str):
        if len(id) > 0:
            return self.transactions(id)
        else:
            print("you forgot the req id")

    def transactions(self, id):
        requisition = self._client.requisition.get_requisition_by_id(id)

        # transactions_list = []
        for acc in requisition["accounts"]:
            account = self._client.account_api(acc)
            print(account.get_metadata())
            with open("cetelem.json", "w") as f:
                dump(account.get_transactions(), f, indent=4)
            # print(dumps(account.get_transactions(), indent=4))

        # print(transactions_list)

    def banks(self, country: str):
        print(self._client.institution.get_institutions(country))

    @property
    def client(self):
        return self._client

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
