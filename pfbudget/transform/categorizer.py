from copy import deepcopy
from typing import Sequence

from pfbudget.db.model import (
    CategoryRule,
    CategorySelector,
    Selector_T,
    Transaction,
    TransactionCategory,
)
from .exceptions import TransactionCategorizedError
from .transform import Transformer


class Categorizer(Transformer):
    def __init__(self, rules: Sequence[CategoryRule]):
        self.rules = rules

    def transform(self, transactions: Sequence[Transaction]) -> Sequence[Transaction]:
        result = deepcopy(transactions)
        self.transform_inplace(result)

        return result

    def transform_inplace(self, transactions: Sequence[Transaction]) -> None:
        for rule in self.rules:
            for transaction in transactions:
                if transaction.category:
                    raise TransactionCategorizedError(transaction)

                if not rule.matches(transaction):
                    continue

                transaction.category = TransactionCategory(
                    rule.name, CategorySelector(Selector_T.rules)
                )
