from datetime import date, timedelta
from functools import singledispatch

from pfbudget.common.types import TransactionError
from pfbudget.db.model import Bank, Transaction
from .utils import parse_decimal


@singledispatch
def convert(t):
    print("No converter as been found")
    pass


@convert.register
def _(json: dict, bank: Bank) -> Transaction:
    i = -1 if bank.nordigen.invert else 1
    try:
        transaction = Transaction(
            date=date.fromisoformat(json["bookingDate"]),
            description=json["remittanceInformationUnstructured"],
            bank=bank.name,
            amount=i * parse_decimal(json["transactionAmount"]["amount"]),
        )
        # transaction.date += timedelta(days=bank.offset)
        return transaction

    except TransactionError:
        print(f"{json} is in the wrong format")
