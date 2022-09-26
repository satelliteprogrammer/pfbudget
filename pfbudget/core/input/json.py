import json

from pfbudget.core.transactions import Transactions
from pfbudget.utils.converters import convert
from pfbudget.utils.utils import parse_decimal

from .input import Input


class JsonParser(Input):
    def __init__(self, options):
        super().__init__(options)

    def transactions(self) -> Transactions:
        with open(self.options["json"][0], "r") as f:
            return [
                convert(
                    [
                        t["bookingDate"],
                        t["remittanceInformationUnstructured"],
                        self.options["bank"][0],
                        parse_decimal(t["transactionAmount"]["amount"])
                        if not self.options["invert"]
                        else -parse_decimal(t["transactionAmount"]["amount"]),
                    ],
                )
                for t in json.load(f)["transactions"]["booked"]
            ]
