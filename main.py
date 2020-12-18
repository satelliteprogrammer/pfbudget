from datetime import date
from pathlib import Path
import argparse
import matplotlib.pyplot as plt
import pickle

from initializer import initialize
from pfbudget.categories import Categories
from pfbudget.transactions import Transaction as Tr, TransactionError, Transactions
from pfbudget.parsers import Parser


p = ".pfbudget.pickle"


class PfBudgetInitialized(Exception):
    pass


class PfBudgetNotInitialized(Exception):
    pass


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


def init(args):
    """init function

    Creates .pfbudget.pickle which stores the internal state of the program for later use. Parses all raw directory
    into data directory.

    args.raw -- raw dir
    args.data -- data dir
    """
    if not Path(p).is_file():
        s = {"filename": p, "raw_dir": args.raw, "data_dir": args.data, "data": []}
        with open(p, "wb") as f:
            pickle.dump(s, f)
        parse(args)
    else:
        raise PfBudgetInitialized()


def restart(args):
    """restart function

    Deletes .pfbudget.pickle and creates new one. Parses all raw directory into data directory. New dirs can be passed
    as arguments, otherwise uses previous values

    args.raw -- raw dir
    args.data -- data dir
    """
    if Path(p).is_file():
        s = pickle.load(open(p, "rb"))
        raw_dir = s["raw_dir"] if not args.raw else args.raw
        data_dir = s["data_dir"] if not args.data else args.data

        s = {"filename": p, "raw_dir": raw_dir, "data_dir": data_dir, "data": []}
        pickle.dump(s, open(p, "wb"))
        parse(args)
    else:
        raise PfBudgetNotInitialized()


def parse(args):
    """parse function

    Extracts from .pfbudget.pickle the already read files and parses the remaining. args will be None if called from
    command line and gathered from the pickle.

    args.raw -- raw dir
    args.data -- data dir
    """
    if not args:
        s = pickle.load(open(p, "rb"))
        raw_dir = s["raw_dir"]
        data_dir = s["data_dir"]
    else:
        raw_dir = args.raw
        data_dir = args.data

    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="does cool finance stuff")
    parser.add_argument("-q", "--quiet", help="quiet")
    subparsers = parser.add_subparsers(help="sub-command help")

    p_init = subparsers.add_parser("init", help="init help")
    p_restart = subparsers.add_parser("restart", help="restart help")
    p_parse = subparsers.add_parser("parse", help="parse help")
    p_graph = subparsers.add_parser("graph", help="graph help")
    p_report = subparsers.add_parser("report", help="report help")

    p_init.add_argument("raw", help="the raw data dir")
    p_init.add_argument("data", help="the parsed data dir")
    p_init.set_defaults(func=init)

    p_restart.add_argument("--raw", help="new raw data dir")
    p_restart.add_argument("--data", help="new parsed data dir")
    p_restart.set_defaults(func=restart)

    p_parse.set_defaults(func=parse)

    args = parser.parse_args()
    args.func(args)

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
