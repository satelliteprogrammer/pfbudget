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

# The simple and simple_transformed match the nordigen mocks
simple = [
    BankTransaction(date(2023, 1, 14), "string", Decimal("328.18"), bank="bank"),
    BankTransaction(date(2023, 2, 14), "string", Decimal("947.26"), bank="bank"),
]

simple_transformed = [
    BankTransaction(
        date(2023, 1, 14),
        "",
        Decimal("328.18"),
        bank="bank",
        category=TransactionCategory("category#1", CategorySelector.algorithm),
    ),
    BankTransaction(
        date(2023, 2, 14),
        "",
        Decimal("947.26"),
        bank="bank",
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
__original.id = 9000

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
