from codetiming import Timer
from datetime import timedelta
from typing import Sequence

import pfbudget.db.model as t


class Categorizer:
    options = {}

    def __init__(self):
        self.options["null_days"] = 4

    def rules(
        self,
        transactions: Sequence[t.BankTransaction],
        categories: Sequence[t.Category],
        tags: Sequence[t.Tag],
    ):
        """Overarching categorization tool

        Receives a list of transactions (by ref) and updates their category according
        to the rules defined for each category

        Args:
            transactions (Sequence[BankTransaction]): uncategorized transactions
            categories (Sequence[Category]): available categories
            tags (Sequence[Tag]): currently available tags
        """

        self._nullify(transactions)

        self._rule_based_categories(transactions, categories)
        self._rule_based_tags(transactions, tags)

    def manual(
        self,
        transactions: Sequence[t.Transaction],
        categories: Sequence[t.Category],
        tags: Sequence[t.Tag],
    ):
        """Manual categorization input

        Args:
            transactions (Sequence[Transaction]): uncategorized transactions
            categories (Sequence[Category]): available categories
            tags (Sequence[Tag]): currently available tags
        """
        self._manual(transactions)

    @Timer(name="nullify")
    def _nullify(self, transactions: Sequence[t.BankTransaction]):
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
                transaction.category = t.TransactionCategory(
                    name="null",
                    selector=t.CategorySelector(t.Selector_T.nullifier),
                )
                cancel.category = t.TransactionCategory(
                    name="null",
                    selector=t.CategorySelector(t.Selector_T.nullifier),
                )
                matching.extend([transaction, cancel])
                count += 2
                break

        print(f"Nullified {count} transactions")

    @Timer(name="categoryrules")
    def _rule_based_categories(
        self,
        transactions: Sequence[t.BankTransaction],
        categories: Sequence[t.Category],
    ):
        d = {}
        for category in [c for c in categories if c.rules]:
            for rule in category.rules:
                # for transaction in [t for t in transactions if not t.category]:
                for transaction in [
                    t
                    for t in transactions
                    if not t.category or t.category.name != "null"
                ]:
                    if not rule.matches(transaction):
                        continue

                    # passed all conditions, assign category
                    if (
                        transaction.category
                        and transaction.category.name == category.name
                    ):
                        if (
                            input(f"Overwrite {transaction} with {category}? (y/n)")
                            == "y"
                        ):
                            transaction.category.name = category.name
                            transaction.category.selector.selector = t.Selector_T.rules
                    else:
                        transaction.category = t.TransactionCategory(
                            category.name, t.CategorySelector(t.Selector_T.rules)
                        )

                    if rule in d:
                        d[rule] += 1
                    else:
                        d[rule] = 1

        for k, v in d.items():
            print(f"{v}: {k}")

    @Timer(name="tagrules")
    def _rule_based_tags(
        self, transactions: Sequence[t.BankTransaction], tags: Sequence[t.Tag]
    ):
        d = {}
        for tag in [t for t in tags if len(t.rules) > 0]:
            for rule in tag.rules:
                # for transaction in [t for t in transactions if not t.category]:
                for transaction in [
                    t
                    for t in transactions
                    if tag.name not in [tag.tag for tag in t.tags]
                ]:
                    if not rule.matches(transaction):
                        continue

                    if not transaction.tags:
                        transaction.tags = {t.TransactionTag(tag.name)}
                    else:
                        transaction.tags.add(t.TransactionTag(tag.name))

                    if rule in d:
                        d[rule] += 1
                    else:
                        d[rule] = 1

        for k, v in d.items():
            print(f"{v}: {k}")

    def _manual(self, transactions: Sequence[t.Transaction]):
        uncategorized = [t for t in transactions if not t.category]
        print(f"{len(uncategorized)} transactions left to categorize")

        for transaction in uncategorized:
            while True:
                category = input(f"{transaction} category: ")
                if category == "quit":
                    return
                if not category:
                    print("{category} doesn't exist")
                    continue
                transaction.category = t.TransactionCategory(
                    category, t.CategorySelector(t.Selector_T.manual)
                )

                break
