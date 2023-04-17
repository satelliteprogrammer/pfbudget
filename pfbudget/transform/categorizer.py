from codetiming import Timer
from datetime import timedelta
from typing import Sequence

import pfbudget.db.model as t


class Categorizer:
    options = {}

    def __init__(self):
        self.options["null_days"] = 3

    def rules(
        self,
        transactions: Sequence[t.BankTransaction],
        categories: Sequence[t.Category],
        tags: Sequence[t.Tag],
        nullify: bool = True
    ):
        """Overarching categorization tool

        Receives a list of transactions (by ref) and updates their category according
        to the rules defined for each category

        Args:
            transactions (Sequence[BankTransaction]): uncategorized transactions
            categories (Sequence[Category]): available categories
            tags (Sequence[Tag]): currently available tags
        """

        if nullify:
            try:
                null = next(cat for cat in categories if cat.name == "null")
                print("Nullifying")
                self._nullify(transactions, null)

            except StopIteration:
                print("Null category not defined")

        categories = [cat for cat in categories if cat.name != "null"]

        self._rule_based_categories(transactions, categories)
        self._rule_based_tags(transactions, tags)

    @Timer(name="nullify")
    def _nullify(self, transactions: Sequence[t.BankTransaction], null: t.Category):
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
                    and cancel != transaction
                    and cancel.bank != transaction.bank
                    and cancel.amount == -transaction.amount
                    and transaction not in matching
                    and cancel not in matching
                    and all(r.matches(transaction) for r in null.rules)
                    and all(r.matches(cancel) for r in null.rules)
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

        print(f"Nullified {count} of {len(transactions)} transactions")

    @Timer(name="categoryrules")
    def _rule_based_categories(
        self,
        transactions: Sequence[t.BankTransaction],
        categories: Sequence[t.Category],
    ):
        print(f"Categorizing {len(transactions)} transactions")
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
                    if transaction.category:
                        if transaction.category.name == category.name:
                            continue

                        if (
                            input(
                                f"Overwrite {transaction} with {category.name}? (y/n)"
                            )
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
        print(f"Tagging {len(transactions)} transactions")
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
