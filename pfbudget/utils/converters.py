import datetime as dt
import functools
from typing import Any

from pfbudget.common.types import TransactionError
import pfbudget.db.model as t

from .utils import parse_decimal


@functools.singledispatch
def convert(t) -> Any:
    print("No converter has been found")
    pass


@convert.register
def _(json: dict, bank: t.Bank) -> t.BankTransaction | None:
    i = -1 if bank.nordigen and bank.nordigen.invert else 1
    try:
        transaction = t.BankTransaction(
            date=dt.date.fromisoformat(json["bookingDate"]),
            description=json["remittanceInformationUnstructured"],
            bank=bank.name,
            amount=i * parse_decimal(json["transactionAmount"]["amount"]),
        )
        # transaction.date += timedelta(days=bank.offset)
        return transaction

    except TransactionError:
        print(f"{json} is in the wrong format")
