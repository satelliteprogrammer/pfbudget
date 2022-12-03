from datetime import date, timedelta
from functools import singledispatch

from pfbudget.common.types import TransactionError
from pfbudget.db.model import Bank, Transaction
from pfbudget.db.schema import DbBank, DbTransaction
from .utils import parse_decimal


@singledispatch
def convert(t):
    print("No converter as been found")
    pass


# @convert.register
# def _(t: Transaction) -> DbTransaction:
#     return DbTransaction(
#         t.date,
#         t.description,
#         t.bank,
#         t.value,
#         t.category,
#         t.original,
#         t.additional_comment,
#     )


# @convert.register
# def _(db: DbTransaction) -> Transaction:
#     try:
#         return Transaction(db)
#     except TransactionError:
#         print(f"{db} is in the wrong format")


# @convert.register
# def _(db: DbBank, key: str = "") -> Bank:
#     bank = Bank(db.name, db.bic, db.requisition_id, db.invert, db.offset, key=key)
#     if not bank.invert:
#         bank.invert = False
#     if not bank.offset:
#         bank.offset = 0
#     return bank


# @convert.register
# def _(bank: Bank) -> DbBank:
#     bank = DbBank(
#         bank.name, bank.bic, "", "", bank.requisition_id, bank.invert, bank.offset
#     )
#     if not bank.invert:
#         bank.invert = False
#     if not bank.offset:
#         bank.offset = 0
#     return bank


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
