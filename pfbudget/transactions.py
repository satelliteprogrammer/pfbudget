from csv import reader, writer
from datetime import date
from dateutil.rrule import rrule, MONTHLY, YEARLY
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .categories import get_categories

COMMENT_TOKEN = "#"


class TransactionError(Exception):
    pass


class Transaction:
    def __init__(self, *args, file=None):
        self.date = None
        self.description = ""
        self.bank = ""
        self.value = 0
        self.category = ""

        arg = args[0] if len(args) == 1 else list(args)
        try:
            self.date = date.fromisoformat(arg[0])
            self.description = " ".join(arg[1].split())
            self.bank = arg[2]
            self.value = Decimal(arg[3])
            self.category = arg[4]
        except IndexError:
            pass
        except InvalidOperation:
            print(f"{args}")
            raise TransactionError

        self.year = self.date.year
        self.month = self.date.month
        self.day = self.date.day

        self.file = file
        self.modified = False

    def to_csv(self):
        return [self.date, self.description, self.bank, self.value, self.category]

    @staticmethod
    def get_repeated_transactions(transactions):
        repeated, new = list(), list()
        for t in transactions:
            if t not in new:
                new.append(t)
            else:
                repeated.append(t)
        return repeated

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


def sort_by_bank(transactions: list):
    transactions.sort(key=lambda k: k.bank)


def daterange(start, end, period):
    if not start or not end:
        raise TransactionError("daterange requires start and end")

    if period == "year":
        r = [d.strftime("%Y") for d in rrule(YEARLY, dtstart=start, until=end)]
    elif period == "month":
        r = [d.strftime("%b %Y") for d in rrule(MONTHLY, dtstart=start, until=end)]
    else:
        raise TransactionError("wrong time period")
    return r


def by_year(transactions, start=None, end=None) -> dict:
    start = start if start else transactions[0].date
    end = end if end else transactions[-1].date

    yearly_transactions = dict.fromkeys(daterange(start, end, "year"), None)
    for t in [t for t in transactions if t.date >= start and t.date <= end]:
        try:
            yearly_transactions[t.date.strftime("%Y")].append(t)
        except AttributeError:
            yearly_transactions[t.date.strftime("%Y")] = [t]
        except KeyError:
            raise TransactionError("date invalid")

    return yearly_transactions


def by_month(transactions, start=None, end=None) -> dict:
    start = start if start else transactions[0].date
    end = end if end else transactions[-1].date

    monthly_transactions = dict.fromkeys(daterange(start, end, "month"), None)
    for t in [t for t in transactions if t.date >= start and t.date <= end]:
        try:
            monthly_transactions[t.date.strftime("%b %Y")].append(t)
        except AttributeError:
            monthly_transactions[t.date.strftime("%b %Y")] = [t]
        except KeyError:
            raise TransactionError("date invalid")

    return monthly_transactions


def by_category(transactions) -> dict:
    transactions_by_category = dict.fromkeys(get_categories(), None)

    if transactions:
        for transaction in transactions:
            try:
                transactions_by_category[transaction.category].append(transaction)
            except AttributeError:
                transactions_by_category[transaction.category] = [transaction]

    return transactions_by_category


def by_year_and_category(transactions, start, end) -> dict:
    yearly_transactions_by_category = {}

    yearly_transactions = by_year(transactions, start, end)
    for year, transactions in yearly_transactions.items():
        yearly_transactions_by_category[year] = by_category(transactions)

    return yearly_transactions_by_category


def by_month_and_category(transactions, start, end) -> dict:
    monthly_transactions_by_categories = {}

    monthly_transactions = by_month(transactions, start, end)
    for month, transactions in monthly_transactions.items():
        monthly_transactions_by_categories[month] = by_category(transactions)

    return monthly_transactions_by_categories


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
