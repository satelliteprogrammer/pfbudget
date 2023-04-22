from copy import deepcopy
from typing import Iterable, Sequence

from pfbudget.db.model import TagRule, Transaction, TransactionTag
from .transform import Transformer


class Tagger(Transformer):
    def __init__(self, rules: Iterable[TagRule]):
        self.rules = rules

    def transform(self, transactions: Sequence[Transaction]) -> Sequence[Transaction]:
        result = deepcopy(transactions)
        self.transform_inplace(result)

        return result

    def transform_inplace(self, transactions: Sequence[Transaction]) -> None:
        for rule in self.rules:
            for transaction in transactions:
                if rule.tag in [tag.tag for tag in transaction.tags]:
                    continue

                if not rule.matches(transaction):
                    continue

                if not transaction.tags:
                    transaction.tags = {TransactionTag(rule.tag)}
                else:
                    transaction.tags.add(TransactionTag(rule.tag))
