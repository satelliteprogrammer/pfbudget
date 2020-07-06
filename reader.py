from decimal import Decimal
import csv
import datetime
import matplotlib.pyplot as plt
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
        self.expense_categories = (
            fixed_expenses_categories + variable_expenses_categories
        )

        self.income_per_cat = dict.fromkeys(income_categories, 0)
        self.fixed_expenses_per_cat = dict.fromkeys(fixed_expenses_categories, 0)
        self.variable_expenses_per_cat = dict.fromkeys(variable_expenses_categories, 0)
        self.null = 0
        self.investments = 0

        self.separate_categories(self.transactions)

        self.expenses_per_cat = {
            **self.income_per_cat,
            **self.fixed_expenses_per_cat,
            **self.variable_expenses_per_cat,
        }

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
{0:>40} Report
Income                     Fixed Expenses             Variable Expenses
{1:<16}{2:>9.2f}  {11:<16}{12:>9.2f}  {25:<16}{26:>9.2f}
{3:<16}{4:>9.2f}  {13:<16}{14:>9.2f}  {27:<16}{28:>9.2f}
{5:<16}{6:>9.2f}  {15:<16}{16:>9.2f}  {29:<16}{30:>9.2f}
{7:<16}{8:>9.2f}  {17:<16}{18:>9.2f}  {31:<16}{32:>9.2f}
{9:<16}{10:>9.2f}  {19:<16}{20:>9.2f}  {33:<16}{34:>9.2f}
                           {21:<16}{22:>9.2f}  {35:<16}{36:>9.2f}
                           {23:<16}{24:>9.2f}  {37:<16}{38:>9.2f}
                                                      {39:<16}{40:>9.2f}
                                                      {41:<16}{42:>9.2f}
                                                      {43:<16}{44:>9.2f}
                                                      {45:<16}{46:>9.2f}
                                                      {47:<16}{48:>9.2f}
                                                      {49:<16}{50:>9.2f}
                                                      {51:<16}{52:>9.2f}

{53:>25.2f}  {54:>25.2f}  {55:>25.2f}

Expenses:{56:>16.2f}
Net:{57:>21.2f}""".format(
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


def plot(monthly_transactions):
    x = range(1, 7)
    y_income = [float(month.income()) for month in monthly_transactions]
    y_fixed_expenses = [float(month.fixed_expenses()) for month in monthly_transactions]
    y_variable_expenses = [
        float(month.variable_expenses()) for month in monthly_transactions
    ]

    y = []
    labels = monthly_transactions[0].expense_categories
    for label in labels:
        category = [
            float(month.expenses_per_cat[label]) for month in monthly_transactions
        ]
        y.append(category)

    no_negatives = False
    while not no_negatives:
        no_negatives = True
        for category in y:
            for month in range(0, 6):
                if category[month] < 0:
                    category[month - 1] += category[month]
                    category[month] = 0
                    no_negatives = False

    plt.plot(x, y_income, label="Income")
    plt.stackplot(x, y, labels=labels)
    plt.legend(loc="upper left")
    plt.show()


if __name__ == "__main__":

    transactions = get_transactions("transactions.csv")

    transactions = reorder_transactions(transactions)

    write_transactions("transactions_ordered.csv", transactions)

    monthly_transactions = list()
    for month in range(1, 7):
        month_transactions = MonthlyTransactions(
            month, get_month_transactions(transactions, month)
        )
        monthly_transactions.append(month_transactions)

        print(month_transactions)

    plot(monthly_transactions)

    total_income = sum(month.income() for month in monthly_transactions)
    total_expenses = sum(month.expenses() for month in monthly_transactions)

    if total_income - total_expenses > 0:
        print(f"\nWe're {total_income - total_expenses} richer!")
    else:
        print(f"We're {total_expenses - total_income} poorer :(")
