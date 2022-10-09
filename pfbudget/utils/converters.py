from functools import singledispatch

from pfbudget.common.types import Transaction, Transactions, TransactionError
from pfbudget.db.schema import DbTransaction, DbTransactions


@singledispatch
def convert(t):
    pass


@convert.register
def _(t: Transaction) -> DbTransaction:
    return (t.date, t.description, t.bank, t.value, t.category)


def convert_dbtransaction(db) -> Transaction:
    try:
        return Transaction(db)
    except TransactionError:
        print(f"{db} is in the wrong format")


convert.register(type(DbTransaction), convert_dbtransaction)


def convert_transactions(ts: Transactions) -> DbTransactions:
    try:
        return [convert(t) for t in ts]
    except TransactionError:
        print(f"{ts} is in the wrong format")


convert.register(type(Transactions), convert_transactions)


def convert_dbtransactions(ts: DbTransactions) -> Transactions:
    try:
        return [convert(t) for t in ts]
    except TransactionError:
        print(f"{ts} is in the wrong format")


convert.register(type(DbTransactions), convert_dbtransactions)
