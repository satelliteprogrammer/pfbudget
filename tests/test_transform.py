from datetime import date
from decimal import Decimal

import mocks.categories as mock

from pfbudget.db.model import (
    Bank,
    BankTransaction,
    CategoryRule,
    CategorySelector,
    Selector_T,
    TransactionCategory,
    TransactionTag,
)
from pfbudget.transform.categorizer import Categorizer
from pfbudget.transform.nullifier import Nullifier
from pfbudget.transform.tagger import Tagger
from pfbudget.transform.transform import Transformer


class TestTransform:
    def test_nullifier(self):
        transactions = [
            BankTransaction(date(2023, 1, 1), "", Decimal("-500"), "Bank#1"),
            BankTransaction(date(2023, 1, 2), "", Decimal("500"), "Bank#2"),
        ]

        for t in transactions:
            assert not t.category

        categorizer: Transformer = Nullifier()
        transactions = categorizer.transform(transactions)

        for t in transactions:
            assert t.category == TransactionCategory(
                "null", CategorySelector(Selector_T.nullifier)
            )

    def test_nullifier_inplace(self):
        transactions = [
            BankTransaction(date(2023, 1, 1), "", Decimal("-500"), "Bank#1"),
            BankTransaction(date(2023, 1, 2), "", Decimal("500"), "Bank#2"),
        ]

        for t in transactions:
            assert not t.category

        categorizer: Transformer = Nullifier()
        categorizer.transform_inplace(transactions)

        for t in transactions:
            assert t.category == TransactionCategory(
                "null", CategorySelector(Selector_T.nullifier)
            )

    def test_nullifier_with_rules(self):
        transactions = [
            BankTransaction(date(2023, 1, 1), "", Decimal("-500"), "Bank#1"),
            BankTransaction(date(2023, 1, 2), "", Decimal("500"), "Bank#2"),
        ]

        for t in transactions:
            assert not t.category

        rules = [CategoryRule(None, None, None, None, "Bank#1", None, None, "null")]

        categorizer: Transformer = Nullifier(rules)
        transactions = categorizer.transform(transactions)

        for t in transactions:
            assert not t.category

        rules.append(CategoryRule(None, None, None, None, "Bank#2", None, None, "null"))
        categorizer: Transformer = Nullifier(rules)
        transactions = categorizer.transform(transactions)

        for t in transactions:
            assert t.category == TransactionCategory(
                "null", CategorySelector(Selector_T.nullifier)
            )

    def test_tagger(self):
        transactions = [
            BankTransaction(date(2023, 1, 1), "desc#1", Decimal("-10"), "Bank#1")
        ]

        for t in transactions:
            assert not t.category

        categorizer = Tagger(mock.tag_1.rules)
        transactions = categorizer.transform(transactions)

        for t in transactions:
            assert TransactionTag("tag#1") in t.tags

    def test_categorize(self):
        transactions = [
            BankTransaction(date(2023, 1, 1), "desc#1", Decimal("-10"), "Bank#1")
        ]

        for t in transactions:
            assert not t.category

        categorizer = Categorizer()
        categorizer.rules(transactions, [mock.category1], [])

        for t in transactions:
            assert t.category == TransactionCategory(
                "cat#1", CategorySelector(Selector_T.rules)
            )
