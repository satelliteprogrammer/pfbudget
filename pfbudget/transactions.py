from csv import reader, writer
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

COMMENT_TOKEN = "#"


class TransactionError(Exception):
    pass


class Transaction:
    def __init__(self, *args, file=None):
        self.date = None
        self.description = ""
        self.bank = ""
        self.value = 0
        self.category = None

        arg = args[0] if len(args) == 1 else list(args)
        try:
            if type(arg[0]) is date:
                self.date = arg[0]
            else:
                self.date = date.fromisoformat(arg[0])
            self.description = " ".join(arg[1].split())
            self.bank = arg[2]
            if type(arg[3]) is float:
                self.value = arg[3]
            else:
                self.value = Decimal(args[3])
            self.category = arg[4]
        except IndexError:
            pass
        except InvalidOperation:
            print(f"{args}")
            raise TransactionError

        self.year = self.date.year
        self.month = self.date.month
        self.day = self.date.day

        self.modified = False

    def to_list(self):
        return [self.date, self.description, self.bank, self.value, self.category]

    def update_category(self):
        return (self.category, self.date, self.description, self.bank, self.value)

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, v):
        self.modified = True
        self._category = v

    def __eq__(self, other):
        return (
            self.date == other.date
            and self.description == other.description
            and self.bank == other.bank
            and self.value == other.value
        )

    def __ne__(self, other):
        return (
            self.date != other.date
            or self.description != other.description
            or self.bank != other.bank
            or self.value != other.value
        )

    def __lt__(self, other):
        return self.date < other.date

    def __le__(self, other):
        return self.date <= other.date

    def __gt__(self, other):
        return self.date > other.date

    def __ge__(self, other):
        return self.date >= other.date

    def desc(self):
        return "{} {} {}€ ({})".format(
            self.date.strftime("%d/%m/%y"), self.description, self.value, self.bank
        )

    def __repr__(self):
        return "{} {} {}€ ({})".format(
            self.date.strftime("%d/%m/%y"), self.category, self.value, self.bank
        )


def load_transactions(data_dir) -> list:
    transactions = []
    for df in Path(data_dir).iterdir():
        try:
            trs = read_transactions(df)
        except TransactionError as e:
            print(f"{e} -> datafile {df}")
            raise TransactionError
        transactions.extend(trs)

    transactions.sort()
    return transactions


def save_transactions(data_dir, transactions):
    files2write = set(t.file if t.modified else None for t in transactions)
    files2write.discard(None)
    for f in files2write:
        trs = [t for t in transactions if t.file == f]
        write_transactions(f, trs)


def read_transactions(filename, encoding="utf-8") -> list:
    try:
        with open(filename, newline="", encoding=encoding) as f:
            r = reader(f, delimiter="\t")
            transactions = [
                Transaction(row, file=filename)
                for row in r
                if row and row[0][0] != COMMENT_TOKEN
            ]
    except FileNotFoundError:
        transactions = []

    return transactions


def write_transactions(file, transactions, append=False, encoding="utf-8"):
    with open(file, "a" if append else "w", newline="", encoding=encoding) as f:
        w = writer(f, delimiter="\t")
        w.writerows([transaction.to_csv() for transaction in transactions])
