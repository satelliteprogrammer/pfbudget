from pfbudget.db.model import Transaction, TransactionCategory

from datetime import timedelta


class Categorizer:
    options = {}

    def __init__(self):
        self.options["null_days"] = 4

    def categorize(self, transactions: list[Transaction]):
        """Overarching categorization tool

        Receives a list of transactions (by ref) and updates their category

        Args:
            transactions (list[Transaction]): uncategorized transactions
        """

        self._nullify(transactions)

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
                transaction.category = TransactionCategory(name="null")
                cancel.category = TransactionCategory(name="null")
                matching.extend([transaction, cancel])
                count += 2
                break

        print(f"Nullified {count} transactions")
