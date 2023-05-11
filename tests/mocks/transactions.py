from datetime import date
from decimal import Decimal

from pfbudget.db.model import (
    BankTransaction,
    CategorySelector,
    MoneyTransaction,
    Note,
    SplitTransaction,
    Transaction,
    TransactionCategory,
    TransactionTag,
)

simple = [
    Transaction(date(2023, 1, 1), "", Decimal("-10")),
    Transaction(date(2023, 1, 2), "", Decimal("-50")),
]

simple_transformed = [
    Transaction(
        date(2023, 1, 1),
        "",
        Decimal("-10"),
        category=TransactionCategory("category#1", CategorySelector.algorithm),
    ),
    Transaction(
        date(2023, 1, 2),
        "",
        Decimal("-50"),
        category=TransactionCategory("category#2", CategorySelector.algorithm),
    ),
]

bank = [
    BankTransaction(date(2023, 1, 1), "", Decimal("-10"), bank="bank#1"),
    BankTransaction(date(2023, 1, 1), "", Decimal("-10"), bank="bank#2"),
]

money = [
    MoneyTransaction(date(2023, 1, 1), "", Decimal("-10")),
    MoneyTransaction(date(2023, 1, 1), "", Decimal("-10")),
]

__original = Transaction(date(2023, 1, 1), "", Decimal("-10"), split=True)
__original.id = 1

split = [
    __original,
    SplitTransaction(date(2023, 1, 1), "", Decimal("-5"), original=__original.id),
    SplitTransaction(date(2023, 1, 1), "", Decimal("-5"), original=__original.id),
]

tagged = [
    Transaction(
        date(2023, 1, 1),
        "",
        Decimal("-10"),
        tags={TransactionTag("tag#1"), TransactionTag("tag#1")},
    )
]

noted = [
    Transaction(
        date(2023, 1, 1),
        "",
        Decimal("-10"),
        note=Note("note#1"),
    )
]
