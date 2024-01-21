from copy import deepcopy
from typing import Iterable, Sequence

from pfbudget.db.model import (
    CategoryRule,
    CategorySelector,
    Transaction,
    TransactionCategory,
    TransactionTag,
)
from .transform import Transformer


class Categorizer(Transformer):
    def __init__(self, rules: Iterable[CategoryRule]):
        self.rules = rules

    def transform(self, transactions: Sequence[Transaction]) -> Sequence[Transaction]:
        result = deepcopy(transactions)
        self.transform_inplace(result)

        return result

    def transform_inplace(self, transactions: Sequence[Transaction]) -> None:
        for rule in self.rules:
            for transaction in transactions:
                if not rule.matches(transaction):
                    continue

                if not transaction.category:
                    transaction.category = TransactionCategory(
                        rule.name, CategorySelector.rules
                    )
                else:
                    if not transaction.tags:
                        transaction.tags = {TransactionTag(rule.name)}
                    else:
                        transaction.tags.add(TransactionTag(rule.name))
