import json

from .input import Input
from pfbudget.common.types import Transactions
from pfbudget.utils import convert, parse_decimal


class JsonParser(Input):
    def __init__(self, options):
        super().__init__(options)

    def parse(self) -> Transactions:
        try:
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
        except KeyError:
            print("No json file defined")
