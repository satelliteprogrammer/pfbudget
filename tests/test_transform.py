from datetime import date
from decimal import Decimal
import pytest

import mocks.categories as mock

from pfbudget.db.model import (
    BankTransaction,
    Category,
    CategoryRule,
    CategorySelector,
    TransactionCategory,
    TransactionTag,
)
from pfbudget.transform.categorizer import Categorizer
from pfbudget.transform.exceptions import MoreThanOneMatchError
from pfbudget.transform.nullifier import Nullifier
from pfbudget.transform.tagger import Tagger
from pfbudget.transform.transform import Transformer


class TestTransform:
    def test_nullifier(self):
        transactions = [
            BankTransaction(date(2023, 1, 1), "", Decimal("-500"), bank="Bank#1"),
            BankTransaction(date(2023, 1, 2), "", Decimal("500"), bank="Bank#2"),
        ]

        for t in transactions:
            assert not t.category

        categorizer: Transformer = Nullifier()
        transactions = categorizer.transform(transactions)

        for t in transactions:
            assert t.category == TransactionCategory("null", CategorySelector.nullifier)

    def test_nullifier_inplace(self):
        transactions = [
            BankTransaction(date(2023, 1, 1), "", Decimal("-500"), bank="Bank#1"),
            BankTransaction(date(2023, 1, 2), "", Decimal("500"), bank="Bank#2"),
        ]

        for t in transactions:
            assert not t.category

        categorizer: Transformer = Nullifier()
        categorizer.transform_inplace(transactions)

        for t in transactions:
            assert t.category == TransactionCategory("null", CategorySelector.nullifier)

    def test_nullifier_inplace_unordered(self):
        transactions = [
            BankTransaction(date(2023, 1, 2), "A2", Decimal("500"), bank="Bank#2"),
            BankTransaction(date(2023, 1, 2), "B1", Decimal("-500"), bank="Bank#1"),
            BankTransaction(date(2023, 1, 1), "A1", Decimal("-500"), bank="Bank#1"),
            BankTransaction(date(2023, 1, 2), "B2", Decimal("500"), bank="Bank#2"),
        ]

        for t in transactions:
            assert not t.category

        categorizer: Transformer = Nullifier()
        with pytest.raises(MoreThanOneMatchError):
            categorizer.transform_inplace(transactions)

    def test_nullifier_inplace_repeated(self):
        transactions = [
            BankTransaction(date(2023, 1, 2), "A1", Decimal("-500"), bank="Bank#1"),
            BankTransaction(date(2023, 1, 2), "A2", Decimal("500"), bank="Bank#2"),
            BankTransaction(date(2023, 1, 2), "B1", Decimal("-500"), bank="Bank#1"),
            BankTransaction(date(2023, 1, 2), "B2", Decimal("500"), bank="Bank#2"),
        ]

        for t in transactions:
            assert not t.category

        categorizer: Transformer = Nullifier()
        with pytest.raises(MoreThanOneMatchError):
            categorizer.transform_inplace(transactions)

    def test_nullifier_with_rules(self):
        transactions = [
            BankTransaction(date(2023, 1, 1), "", Decimal("-500"), bank="Bank#1"),
            BankTransaction(date(2023, 1, 2), "", Decimal("500"), bank="Bank#2"),
        ]

        for t in transactions:
            assert not t.category

        rule = CategoryRule(bank="Bank#1")
        rule.name = "null"
        rules = [rule]

        categorizer: Transformer = Nullifier(rules)
        transactions = categorizer.transform(transactions)

        for t in transactions:
            assert not t.category

        rule = CategoryRule(bank="Bank#2")
        rule.name = "null"
        rules.append(rule)
        categorizer = Nullifier(rules)
        transactions = categorizer.transform(transactions)

        for t in transactions:
            assert t.category == TransactionCategory("null", CategorySelector.nullifier)

    def test_tagger(self):
        transactions = [
            BankTransaction(date(2023, 1, 1), "desc#1", Decimal("-10"), bank="Bank#1")
        ]

        for t in transactions:
            assert not t.category

        rules = mock.tag_1.rules
        for rule in rules:
            rule.tag = mock.tag_1.name

        categorizer: Transformer = Tagger(rules)
        transactions = categorizer.transform(transactions)

        for t in transactions:
            assert TransactionTag("tag#1") in t.tags

    def test_categorize(self):
        transactions = [
            BankTransaction(date(2023, 1, 1), "desc#1", Decimal("-10"), bank="Bank#1")
        ]

        for t in transactions:
            assert not t.category

        rules = mock.category1.rules
        for rule in rules:
            rule.name = mock.category1.name

        categorizer: Transformer = Categorizer(rules)
        transactions = categorizer.transform(transactions)

        for t in transactions:
            assert t.category == TransactionCategory("cat#1", CategorySelector.rules)

    def test_rule_limits(self):
        transactions = [
            BankTransaction(date.today(), "", Decimal("-60"), bank="Bank#1"),
            BankTransaction(date.today(), "", Decimal("-120"), bank="Bank#1"),
        ]

        cat = Category("cat")
        cat.rules = [CategoryRule(min=-120, max=-60)]
        for r in cat.rules:
            r.name = cat.name

        transactions = Categorizer(cat.rules).transform(transactions)
        assert all(t.category.name == cat.name for t in transactions)
