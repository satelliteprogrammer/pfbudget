from functools import singledispatch

from pfbudget.common.types import Bank, Transaction, TransactionError
from pfbudget.db.schema import DbBank, DbTransaction
from .utils import parse_decimal


@singledispatch
def convert(t):
    print("No converter as been found")
    pass


@convert.register
def _(t: Transaction) -> DbTransaction:
    return (t.date, t.description, t.bank, t.value, t.category)


@convert.register
def _(db: DbTransaction) -> Transaction:
    try:
        return Transaction(db)
    except TransactionError:
        print(f"{db} is in the wrong format")


@convert.register
def _(db: DbBank, key: str = "") -> Bank:
    return Bank(db.name, db.bic, db.requisition_id, db.invert, key=key)


@convert.register
def _(bank: Bank, key: str = "") -> DbBank:
    return DbBank(bank.name, bank.bic, "", "", bank.requisition_id, bank.invert)


@convert.register
def _(json: dict, bank: str, invert: bool) -> Transaction:
    i = -1 if invert else 1
    try:
        return Transaction(
            json["bookingDate"],
            json["remittanceInformationUnstructured"],
            bank,
            i * parse_decimal(json["transactionAmount"]["amount"]),
        )
    except TransactionError:
        print(f"{json} is in the wrong format")
