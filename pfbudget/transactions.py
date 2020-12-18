from csv import reader, writer
from datetime import date
from decimal import Decimal, InvalidOperation

from .categories import Categories

class TransactionError(Exception):
    pass


class Transaction:
    date = None
    description = ""
    bank = ""
    value = 0
    category = ""

    def __init__(self, *args):
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

    def to_csv(self):
        return [self.date, self.description, self.bank, self.value, self.category]

    @staticmethod
    def read_transactions(file, encoding="utf-8"):
        with open(file, newline="", encoding=encoding) as f:
            r = reader(f, delimiter="\t")
            transactions = [Transaction(row) for row in r if row and row[0][0] != "#"]
        return transactions

    @staticmethod
    def write_transactions(file, transactions, append=False, encoding="utf-8"):
        with open(file, "a" if append else "w", newline="", encoding=encoding) as f:
            w = writer(f, delimiter="\t")
            w.writerows([transaction.to_csv() for transaction in transactions])

    @staticmethod
    def get_repeated_transactions(transactions):
        repeated, new = list(), list()
        for t in transactions:
            if t not in new:
                new.append(t)
            else:
                repeated.append(t)
        return repeated

    @staticmethod
    def sort_by_bank(transactions):
        transactions.sort(key=lambda k: k.bank)
        return transactions

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


class Transactions(list):
    def sort_by_bank(self):
        self.sort(key=lambda k: k.bank)

    def get_transactions_by_year(self, start=None, end=None):
        if not start:
            start = self[0].date
        if not end:
            end = self[-1].date

        years = dict()
        for year in range(start.year, end.year + 1):
            years[year] = Transactions(
                t for t in self if start <= t.date <= end and t.date.year == year
            )

        return years

    def get_transactions_by_month(self, start=None, end=None):
        if not start:
            start = self[0].date
        if not end:
            end = self[-1].date

        months = dict()
        for year, year_transactions in self.get_transactions_by_year(
            start, end
        ).items():
            for month in range(1, 13):
                key = "_".join([str(year), str(month)])
                months[key] = Transactions(
                    t for t in year_transactions if t.date.month == month
                )

        # trims last unused months
        trim = 1
        for transactions in reversed(months.values()):
            if transactions:
                break
            else:
                trim += 1
        while trim := trim - 1:
            months.popitem()

        return months

    def get_transactions_by_category(self):
        categories = {cat: [] for cat in Categories.get_categories_names()}
        for transaction in self:
            try:
                categories[transaction.category].append(transaction)
            except AttributeError:
                categories[transaction.category] = [transaction]
        return categories
