from functools import singledispatch

from pfbudget.core.transactions import Transaction


@singledispatch
def convert(t):
    pass


@convert.register
def _(t: Transaction) -> list:
    return (t.date, t.description, t.bank, t.value, t.category)


@convert.register
def _(transactions: list) -> list[list]:
    return [convert(c) for c in transactions]
