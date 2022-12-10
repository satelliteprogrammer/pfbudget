from pfbudget.db.model import (
    Category,
    CategorySelector,
    Selector,
    Transaction,
    TransactionCategory,
)

from datetime import timedelta
import re


class Categorizer:
    options = {}

    def __init__(self):
        self.options["null_days"] = 4

    def categorize(self, transactions: list[Transaction], categories: list[Category]):
        """Overarching categorization tool

        Receives a list of transactions (by ref) and updates their category

        Args:
            transactions (list[Transaction]): uncategorized transactions
        """

        self._nullify(transactions)
        self._rules(transactions, categories)

    def _nullify(self, transactions: list[Transaction]):
        count = 0
        matching = []
        for transaction in transactions:
            for cancel in (
                cancel
                for cancel in transactions
                if (
                    transaction.date - timedelta(days=self.options["null_days"])
                    <= cancel.date
                    <= transaction.date + timedelta(days=self.options["null_days"])
                    and transaction not in matching
                    and cancel not in matching
                    and cancel != transaction
                    and cancel.bank != transaction.bank
                    and cancel.amount == -transaction.amount
                )
            ):
                transaction.category = TransactionCategory(
                    name="null", selector=CategorySelector(Selector.nullifier)
                )
                cancel.category = TransactionCategory(
                    name="null", selector=CategorySelector(Selector.nullifier)
                )
                matching.extend([transaction, cancel])
                count += 2
                break

        print(f"Nullified {count} transactions")

    def _rules(self, transactions: list[Transaction], categories: list[Category]):
        for category in [c for c in categories if c.rules]:
            for rule in category.rules:
                for transaction in [t for t in transactions if not t.category]:
                    if rule.date:
                        if rule.date < transaction.date:
                            continue
                    if rule.description and transaction.description:
                        if rule.description not in transaction.description:
                            continue
                    if rule.regex and transaction.description:
                        p = re.compile(rule.regex, re.IGNORECASE)
                        if not p.search(transaction.description):
                            continue
                    if rule.bank:
                        if rule.bank != transaction.bank:
                            continue
                    if rule.min_amount:
                        if rule.min_amount > transaction.amount:
                            continue
                    if rule.max_amount:
                        if rule.max_amount <= transaction.amount:
                            continue

                    # passed all conditions, assign category
                    transaction.category = TransactionCategory(
                        category.name, CategorySelector(Selector.rules)
                    )
