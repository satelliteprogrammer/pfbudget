from datetime import date
from decimal import Decimal

from pfbudget.db.model import (
    CategorySelector,
    Transaction,
    TransactionCategory,
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
