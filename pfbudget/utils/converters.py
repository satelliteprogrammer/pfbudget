from functools import singledispatch

from pfbudget.core.transactions import Transaction, TransactionError, Transactions


@singledispatch
def convert(t):
    pass


@convert.register
def _(t: Transaction) -> list:
    return (t.date, t.description, t.bank, t.value, t.category)


@convert.register
def _(t: list) -> Transaction:
    try:
        return Transaction(t)
    except TransactionError:
        print(f"{t} is in the wrong format")


def convert_transactions(transactions) -> list[list]:
    return [convert(c) for c in transactions]


convert.register(type(Transactions), convert_transactions)
