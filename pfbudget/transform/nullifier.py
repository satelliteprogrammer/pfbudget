from copy import deepcopy
import datetime as dt
from typing import Iterable, Sequence

from .exceptions import MoreThanOneMatchError
from .transform import Transformer
from pfbudget.db.model import (
    CategorySelector,
    Transaction,
    TransactionCategory,
)


class Nullifier(Transformer):
    NULL_DAYS = 4

    def __init__(self, rules=None):
        self.rules = rules if rules else []

    def transform(self, transactions: Iterable[Transaction]) -> Sequence[Transaction]:
        """transform

        Find transactions that nullify each others, e.g. transfers between banks or
        between bank and credit cards.

        Args:
            transactions (Sequence[Transaction]): sequence of transactions

        Raises:
            MoreThanOneMatchError: if there is more than a match for a single transation

        Returns:
            Sequence[Transaction]: nullified sequence of transactions
        """

        result = sorted(deepcopy(transactions))

        for i, transaction in enumerate(result[:-1]):
            if matches := [t for t in result[i + 1 :] if self._cancels(transaction, t)]:
                if len(matches) > 1:
                    raise MoreThanOneMatchError(f"{transaction} -> {matches}")

                match = matches[0]

                transaction = self._nullify(transaction)
                match = self._nullify(match)

        return result

    def transform_inplace(self, transactions: Iterable[Transaction]) -> None:
        """transform_inplace

        Find transactions that nullify each others, e.g. transfers between banks or
        between bank and credit cards.

        Args:
            transactions (Sequence[Transaction]): sequence of transactions that will be
            modified inplace

        Raises:
            MoreThanOneMatchError: if there is more than a match for a single transation
        """

        for transaction in sorted(transactions):
            if matches := [t for t in transactions if self._cancels(transaction, t)]:
                if len(matches) > 1:
                    raise MoreThanOneMatchError(f"{transaction} -> {matches}")

                match = matches[0]

                self._nullify(transaction)
                self._nullify(match)

    def _cancels(self, transaction: Transaction, cancel: Transaction):
        return (
            transaction.date
            <= cancel.date
            <= transaction.date + dt.timedelta(days=self.NULL_DAYS)
            and cancel != transaction
            and cancel.bank != transaction.bank
            and cancel.amount == -transaction.amount
            # even though this class receives uncategorized transactions, they may have
            # already been nullified before reaching here
            and not transaction.category
            and (not cancel.category or cancel.category.name != "null")
            and (
                any(r.matches(transaction) for r in self.rules) if self.rules else True
            )
            and (any(r.matches(cancel) for r in self.rules) if self.rules else True)
        )

    def _nullify(self, transaction: Transaction) -> Transaction:
        transaction.category = TransactionCategory(
            "null", selector=CategorySelector.nullifier
        )
        return transaction
