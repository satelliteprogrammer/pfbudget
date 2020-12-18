from datetime import date
from pathlib import Path
import logging
import matplotlib.pyplot as plt
import pickle
import sys

from initializer import initialize
from categories import Categories
from transaction import Transaction as Tr, TransactionError, Transactions
from parsers import Parser


def manual_categorization(trs):
    trs.sort_by_bank()
    for i, transaction in enumerate(trs):
        if not transaction.category:
            category = input(f"{transaction.desc()} category: ")
            if category == "stop":
                break
            if category:
                transaction.category = category
                trs[i] = transaction

    trs.sort()


if __name__ == "__main__":
    # logging.basicConfig(level=logging.DEBUG)

    datafiles = initialize("raw", "data", restart=False)

    transactions = Transactions()
    for file in datafiles.values():
        transactions.extend(file)
    transactions.sort()

    # reprocess = [Education().name]
    # for i, transaction in enumerate(transactions):
    #     for category in Categories.get_categories():
    #         if transaction.category in reprocess:
    #             transaction.category = ''

    if False:
        Categories.categorize(transactions)
        manual_categorization(transactions)

        for f, file in datafiles.items():
            file_transactions = [t for t in transactions if t in file]
            Tr.write_transactions(Path("data") / f, file_transactions)

        Tr.write_transactions("transactions.csv", transactions)

    monthly_transactions = transactions.get_transactions_by_month(
        start=date(2019, 1, 1), end=date(2020, 11, 30)
    )
    monthly_transactions_by_cat = []
    for month_transactions in monthly_transactions.values():
        cat = month_transactions.get_transactions_by_category()
        monthly_transactions_by_cat.append(cat)

    for month, month_transactions in zip(
        monthly_transactions.keys(), monthly_transactions_by_cat
    ):
        nulls = sum(t.value for t in month_transactions["Null"])
        if nulls != 0:
            print(f"{month} {nulls}")

    expense_categories = [
        *Categories.get_fixed_expenses(),
        *Categories.get_variable_expenses(),
        *Categories.get_discretionary_expenses(),
    ]

    if True:
        t = list(monthly_transactions.keys())
        income = [
            float(
                sum(
                    t.value
                    for cat, transactions in months.items()
                    for t in transactions
                    if cat in Categories.get_income_categories()
                )
            )
            for months in monthly_transactions_by_cat
        ]
        # income = []
        # for months in monthly_transactions_by_cat:
        #     for cat, transactions in months.items():
        #         if cat in Categories.get_income_categories():
        #             income.append(sum(transactions))

        expenses = []
        for category in expense_categories:
            expense_value = [
                -float(sum(t.value for t in month[category]))
                for month in monthly_transactions_by_cat
            ]
            expenses.append(expense_value)
        # expenses = [transactions for months in monthly_transactions_by_cat for cat, transactions in months.items()
        #             if cat not in Categories.get_income_categories() and transactions]
        for expense in expenses:
            for i, month in reversed(list(enumerate(t))):
                if expense[i] < 0:
                    if i - 1 < 0:
                        break
                    else:
                        expense[i - 1] += expense[i]
                        expense[i] = 0

        plt.plot(t, income, label="Income")
        plt.stackplot(t, expenses, labels=expense_categories)
        plt.legend(bbox_to_anchor=(1, 1), loc="upper left")
        plt.show()

    income = [
        sum(
            t.value
            for cat, transactions in months.items()
            for t in transactions
            if cat in Categories.get_income_categories()
        )
        for months in monthly_transactions_by_cat
    ]

    expenses = []
    for category in expense_categories:
        expense_value = [
            -sum(t.value for t in month[category])
            for month in monthly_transactions_by_cat
        ]
        expenses.extend(expense_value)

    print(
        "Income: {}, Expenses: {}, Net = {}".format(
            sum(income), sum(expenses), sum(income) - sum(expenses)
        )
    )
