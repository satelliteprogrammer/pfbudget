from datetime import date
from decimal import Decimal

import mocks.categories as mock

from pfbudget.db.model import (
    Bank,
    BankTransaction,
    CategorySelector,
    Selector_T,
    TransactionCategory,
)
from pfbudget.transform.categorizer import Categorizer


class TestTransform:
    def test_nullify(self):
        transactions = [
            BankTransaction(
                date(2023, 1, 1), "", Decimal("-500"), Bank("Bank#1", "", "")
            ),
            BankTransaction(
                date(2023, 1, 2), "", Decimal("500"), Bank("Bank#2", "", "")
            ),
        ]

        for t in transactions:
            assert not t.category

        categorizer = Categorizer()
        categorizer.rules(transactions, [mock.category_null], [])

        for t in transactions:
            assert t.category == TransactionCategory(
                "null", CategorySelector(Selector_T.nullifier)
            )

    def test_categorize(self):
        transactions = [
            BankTransaction(date(2023, 1, 1), "desc#1", Decimal("-10"), "Bank#1")
        ]

        for t in transactions:
            assert not t.category

        categorizer = Categorizer()
        categorizer.rules(transactions, [mock.category_cat1], [])

        for t in transactions:
            assert t.category == TransactionCategory(
                "cat#1", CategorySelector(Selector_T.rules)
            )
