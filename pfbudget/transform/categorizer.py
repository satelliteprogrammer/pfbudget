from codetiming import Timer
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

        categories = [cat for cat in categories if cat.name != "null"]

        self._rule_based_categories(transactions, categories)

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
