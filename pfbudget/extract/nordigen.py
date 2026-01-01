from dataclasses import dataclass
import datetime as dt
import dotenv
import json
import nordigen
import os
import requests
import time
from typing import Any, Optional, Sequence, Tuple
import uuid

from pfbudget.db.client import Client
from pfbudget.db.model import Nordigen

from .exceptions import CredentialsError, DownloadError

dotenv.load_dotenv()


@dataclass
class NordigenCredentials:
    id: str
    key: str

    def valid(self) -> bool:
        return len(self.id) != 0 and len(self.key) != 0


class NordigenClient:
    redirect_url = "https://murta.dev"

    def __init__(self, credentials: NordigenCredentials, client: Client):
        if not credentials.valid():
            raise CredentialsError

        self.__client = nordigen.NordigenClient(
            secret_key=credentials.key, secret_id=credentials.id, timeout=5
        )
        self.__client.token = self.__token(client)

    def download(self, requisition_id) -> Sequence[dict[str, Any]]:
        try:
            requisition = self.__client.requisition.get_requisition_by_id(
                requisition_id
            )
            print(requisition)
        except requests.HTTPError as e:
            raise DownloadError(e)

        transactions = []
        for acc in requisition["accounts"]:
            account = self.__client.account_api(acc)

            retries = 0
            downloaded = None
            while retries < 3:
                try:
                    downloaded = account.get_transactions()
                    break
                except requests.ReadTimeout:
                    retries += 1
                    print(f"Request #{retries} timed-out, retrying in 1s")
                    time.sleep(1)
                except requests.HTTPError as e:
                    if (
                        e.response.status_code == 409
                        and e.response.type == "AccountProcessing"
                    ):
                        timeout = 1
                        while account.get_metadata()["status"] != "READY":
                            print(f"Waiting for status ready, retrying in {timeout}s")
                            time.sleep(timeout)
                            timeout *= 2
                    elif e.response.status_code == 429:
                        print("Rate limit exceeded for today, aborting")
                        break
                    else:
                        raise DownloadError(e)

            if not downloaded:
                print(f"Couldn't download transactions for {account.get_metadata()}")
                continue

            with open(
                f"logs/{dt.datetime.now().isoformat()}_{requisition_id}.json",
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(downloaded, f, ensure_ascii=False, indent=4)

            if (
                "transactions" not in downloaded
                or "booked" not in downloaded["transactions"]
            ):
                print(f"{account} doesn't have transactions")
                continue

            transactions.extend(downloaded["transactions"]["booked"])

        return transactions

    def dump(self, bank, downloaded):
        # @TODO log received JSON
        pass

    def new_requisition(
        self,
        institution_id: str,
        max_historical_days: Optional[int] = None,
        access_valid_for_days: Optional[int] = None,
    ) -> Tuple[str, str]:
        kwargs = {
            "max_historical_days": max_historical_days,
            "access_valid_for_days": access_valid_for_days,
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        req = self.__client.initialize_session(
            self.redirect_url, institution_id, str(uuid.uuid4()), **kwargs
        )
        return req.link, req.requisition_id

    def country_banks(self, country: str):
        return self.__client.institution.get_institutions(country)

    def __token(self, client: Client) -> str:
        with client.session as session:
            token = session.select(Nordigen)

            def datetime(seconds: int) -> dt.datetime:
                return dt.datetime.now() + dt.timedelta(seconds=seconds)

            if not len(token):
                print("First time nordigen token setup")
                new = self.__client.generate_token()
                session.insert(
                    [
                        Nordigen(
                            "access",
                            new["access"],
                            datetime(new["access_expires"]),
                        ),
                        Nordigen(
                            "refresh",
                            new["refresh"],
                            datetime(new["refresh_expires"]),
                        ),
                    ]
                )

                return new["access"]

            else:
                access = next(t for t in token if t.type == "access")
                refresh = next(t for t in token if t.type == "refresh")

                if access.expires > dt.datetime.now():
                    pass
                elif refresh.expires > dt.datetime.now():
                    new = self.__client.exchange_token(refresh.token)
                    access.token = new["access"]
                    access.expires = datetime(new["access_expires"])
                else:
                    new = self.__client.generate_token()
                    access.token = new["access"]
                    access.expires = datetime(new["access_expires"])
                    refresh.token = new["refresh"]
                    refresh.expires = datetime(new["refresh_expires"])

                return access.token


class NordigenCredentialsManager:
    default = NordigenCredentials(
        os.environ.get("SECRET_ID", ""),
        os.environ.get("SECRET_KEY", ""),
    )
