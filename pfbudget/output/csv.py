from csv import DictReader, writer

from pfbudget.db.model import (
    BankTransaction,
    MoneyTransaction,
    Transaction,
)

from .output import Output


class CSV(Output):
    def __init__(self, filename: str):
        self.fn = filename

    def load(self) -> list[Transaction]:
        with open(self.fn, "r", newline="") as f:
            r = DictReader(f)
            return [
                BankTransaction(
                    row["date"], row["description"], row["amount"], False, row["bank"]
                )
                if row["bank"]
                else MoneyTransaction(
                    row["date"], row["description"], False, row["amount"]
                )
                for row in r
            ]

    def report(self, transactions: list[Transaction]):
        with open(self.fn, "w", newline="") as f:
            w = writer(f, delimiter="\t")
            w.writerows(
                [(t.date, t.description, t.amount, t.bank) for t in transactions]
            )
