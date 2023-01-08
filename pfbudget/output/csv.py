from csv import writer

from pfbudget.db.model import Transaction

from .output import Output


class CSV(Output):
    def __init__(self, filename: str):
        self.fn = filename

    def report(self, transactions: list[Transaction]):
        with open(self.fn, "w", newline="") as f:
            w = writer(f, delimiter="\t")
            w.writerows(
                [(t.date, t.description, t.amount, t.bank) for t in transactions]
            )
