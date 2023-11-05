from datetime import date
from typing import Sequence

from pfbudget.db.model import Bank, BankTransaction
from pfbudget.utils.converters import convert

from .exceptions import BankError, DownloadError, ExtractError
from .extract import Extractor
from .nordigen import NordigenClient


class PSD2Extractor(Extractor):
    def __init__(self, client: NordigenClient):
        self.__client = client

    def extract(
        self, bank: Bank, start: date = date.min, end: date = date.max
    ) -> Sequence[BankTransaction]:
        if not bank.nordigen:
            raise BankError("Bank doesn't have Nordigen info")

        try:
            print(f"Downloading from {bank}...")
            downloaded = self.__client.download(bank.nordigen.requisition_id)
        except DownloadError as e:
            print(f"There was an issue downloading from {bank.name}\n{e}")
            raise ExtractError(e)

        self.__client.dump(bank, downloaded)

        return [
            t
            for t in self.convert(bank, downloaded, start, end)
            if start <= t.date <= end
        ]

    def convert(self, bank, downloaded, start, end):
        return [convert(t, bank) for t in downloaded]
