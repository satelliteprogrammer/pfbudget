from pfbudget.db.model import (
    Category,
    CategorySelector,
    Selector,
    Tag,
    Transaction,
    TransactionCategory,
    TransactionTag,
)

from datetime import timedelta


class Categorizer:
    options = {}

    def __init__(self):
        self.options["null_days"] = 4

    def categorize(
        self,
        transactions: list[Transaction],
        categories: list[Category],
        tags: list[Tag],
    ):
        """Overarching categorization tool

        Receives a list of transactions (by ref) and updates their category

        Args:
            transactions (list[Transaction]): uncategorized transactions
        """

        self._nullify(transactions)
        self._rule_based_categories(transactions, categories)
        self._rule_based_tags(transactions, tags)

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

    def _rule_based_categories(
        self, transactions: list[Transaction], categories: list[Category]
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
                    transaction.category = TransactionCategory(
                        category.name, CategorySelector(Selector.rules)
                    )

                    if rule in d:
                        d[rule] += 1
                    else:
                        d[rule] = 1

        for k, v in d.items():
            print(f"{v}: {k}")

    def _rule_based_tags(self, transactions: list[Transaction], tags: list[Tag]):
        d = {}
        for tag in [t for t in tags if t.rules]:
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
                        transaction.tags = {TransactionTag(tag.name)}
                    else:
                        transaction.tags.add(TransactionTag(tag.name))

                    if rule in d:
                        d[rule] += 1
                    else:
                        d[rule] = 1

        for k, v in d.items():
            print(f"{v}: {k}")

