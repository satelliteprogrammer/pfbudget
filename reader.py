from decimal import Decimal
import csv
import datetime
import sys


class Transaction:
    def __init__(self, date, description, value, category):
        self.id = id(self)
        self.date = date
        self.description = description
        self.value = value
        self.category = category

    def __repr__(self):
        return f"{self.date.date()} {self.description} {self.value} €  {self.category}"


class MonthlyTransactions:
    def __init__(self, month, transactions):
        self.month = datetime.datetime.strptime(str(month), "%m")
        self.transactions = transactions

        income_categories = [
            "Income1",
            "Income2",
            "Income3",
        ]
        fixed_expenses_categories = [
            "Rent",
            "Commmute",
            "Utilities",
        ]
        variable_expenses_categories = [
            "Groceries",
            "Eating Out",
            "Entertainment",
            "Pets",
            "Travel",
            "Miscellaneous",
        ]

        self.income_per_cat = dict.fromkeys(income_categories, 0)
        self.fixed_expenses_per_cat = dict.fromkeys(fixed_expenses_categories, 0)
        self.variable_expenses_per_cat = dict.fromkeys(variable_expenses_categories, 0)
        self.null = 0
        self.investments = 0

        self.separate_categories(self.transactions)

    def separate_categories(self, transactions):
        for transaction in transactions:
            if transaction.category == "Null":
                self.null += transaction.value
                continue
            if transaction.category == "Investment":
                self.investments += transaction.value
                continue
            try:
                self.income_per_cat[transaction.category] -= transaction.value
                continue
            except KeyError:
                pass
            try:
                self.fixed_expenses_per_cat[transaction.category] += transaction.value
                continue
            except KeyError:
                pass
            try:
                self.variable_expenses_per_cat[
                    transaction.category
                ] += transaction.value
                continue
            except KeyError as e:
                if ", " in transaction.category:
                    categories = transaction.category.split(", ")
                    print(f"{transaction} has two categories. Allocate each.")
                    values = []

                    while transaction.value != sum(values):
                        for category in categories:
                            value = Decimal(input(f"Category {category}: "))
                            values.append(value)

                    new_transactions = []
                    for value, category in zip(values, categories):
                        new_transactions.append(
                            Transaction(
                                transaction.date,
                                transaction.description,
                                value,
                                category,
                            )
                        )

                    self.separate_categories(new_transactions)

                else:
                    print(repr(e))
                    print(transaction)
                    sys.exit(2)

    def income(self):
        return sum(self.income_per_cat.values())

    def fixed_expenses(self):
        return sum(self.fixed_expenses_per_cat.values())

    def variable_expenses(self):
        return sum(self.variable_expenses_per_cat.values())

    def expenses(self):
        return self.fixed_expenses() + self.variable_expenses()

    def __repr__(self):
        info = []
        for k, v in self.income_per_cat.items():
            info.extend([k, v])
        for k, v in self.fixed_expenses_per_cat.items():
            info.extend([k, v])
        for k, v in self.variable_expenses_per_cat.items():
            info.extend([k, v])

        p = """
\t\t\t\t{0} Report
Income\t\t\tFixed Expenses\t\tVariable Expenses
{1}\t{2}\t{11}\t\t{12}\t{25}\t\t{26}
{3}\t{4}\t{13}\t{14}\t{27}\t{28}
{5}\t{6}\t{15}\t{16}\t{29}\t{30}
{7}\t{8}\t{17}\t\t{18}\t{31}\t{32}
{9}\t{10}\t{19}\t\t{20}\t{33}\t{34}
\t\t\t{21}\t\t{22}\t{35}\t\t{36}
\t\t\t{23}\t{24}\t{37}\t\t{38}
\t\t\t\t\t\t{39}\t\t{40}
\t\t\t\t\t\t{41}\t\t{42}
\t\t\t\t\t\t{43}\t\t{44}
\t\t\t\t\t\t{45}\t\t{46}
\t\t\t\t\t\t{47}\t{48}
\t\t\t\t\t\t{49}\t\t{50}
\t\t\t\t\t\t{51}\t{52}

\t\t{53}\t\t\t{54}\t\t\t{55}

Expenses:\t{56}
Net:\t\t{57}
        """.format(
            self.month.strftime("%B"),
            *info,
            self.income(),
            self.fixed_expenses(),
            self.variable_expenses(),
            self.expenses(),
            self.income() - self.expenses(),
        )

        return p


def get_transactions(csvfile):
    with open(csvfile, newline="") as fp:
        reader = csv.reader(fp, delimiter="\t")

        transactions = []

        for transaction in reader:
            try:
                # date = datetime.datetime.strptime(transaction[0], "%Y-%m-%d")
                date = datetime.datetime.strptime(transaction[0], "%d/%m/%Y")
                description = transaction[1]
                value = Decimal(transaction[2])
                category = transaction[3]
                transactions.append(Transaction(date, description, value, category))

            except Exception as e:
                print(repr(e))
                print(transaction)
                sys.exit(2)

    return transactions


def reorder_transactions(transactions):
    return sorted(transactions, key=lambda transaction: transaction.date)


def write_transactions(csvfile, transactions):
    with open(csvfile, "w", newline="") as fp:
        writer = csv.writer(fp, delimiter="\t")

        for t in transactions:
            writer.writerow([t.date.date(), t.description, t.value, t.category])


def get_month_transactions(transactions, month):
    month_transactions = []
    for transaction in transactions:
        if transaction.date.month == month:
            month_transactions.append(transaction)

    return month_transactions


def get_value_per_category(transactions):
    categories = dict()

    for transaction in transactions:
        try:
            categories[transaction.category] += transaction.value
        except KeyError:
            categories[transaction.category] = transaction.value

    return categories


def split_income_expenses(value_per_category):
    income = dict()
    expenses = dict()

    for category, value in value_per_category.items():
        if category.startswith("Income"):
            income[category] = -value
        elif category == "Investment":
            pass
        else:
            expenses[category] = value

    return income, expenses


if __name__ == "__main__":

    transactions = get_transactions("transactions.csv")

    transactions = reorder_transactions(transactions)

    write_transactions("transactions_ordered.csv", transactions)

    monthly_transactions = list()
    monthly_categories = list()
    incomes = list()
    expenses = list()
    for month in range(1, 7):
        month_transactions = MonthlyTransactions(
            month, get_month_transactions(transactions, month)
        )
        monthly_transactions.append(month_transactions)

        print(month_transactions)

    total_income = sum(month.income() for month in monthly_transactions)
    total_expenses = sum(month.expenses() for month in monthly_transactions)
    if total_income - total_expenses > 0:
        print(f"\nWe're {total_income - total_expenses} richer!")
    else:
        print(f"We're {total_expenses - total_income} poorer :(")
