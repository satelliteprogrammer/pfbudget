from datetime import date
from pathlib import Path
import logging
import matplotlib.pyplot as plt
import pickle
import sys

from categories import Categories
from transaction import Transaction as Tr, TransactionError, Transactions
from parsers import Parser


def get_transactions(data_dir):
    dfs = dict()
    for df in Path(data_dir).iterdir():
        try:
            trs = Tr.read_transactions(df)
        except TransactionError as e:
            print(f"{e} -> datafile {df}")
            sys.exit(-2)
        dfs[df.name] = trs

    return dfs


def initialize(raw_dir, data_dir, restart=False):
    dfs = get_transactions(data_dir)
    if restart:
        rfs = dict()
        logging.debug("rewriting both .raw and .transactions pickles")
    else:
        try:
            rfs = pickle.load(open(".raw.pickle", "rb"))
            assert (
                type(rfs) is dict
            ), ".raw.pickle isn't a dictionary, so it could have been corrupted"
            logging.debug(".raw.pickle opened")
        except FileNotFoundError:
            rfs = dict()
            logging.debug("no .raw.pickle found")

    updated_trs, update = dict(), False
    prompt = " has been modified since last update. Do you want to update the data files? (Yes/No)"
    for rf in Path(raw_dir).iterdir():
        if rf.name in rfs and rfs[rf.name][0] == rf.stat().st_mtime:
            logging.debug(f"{rf.name} hasn't been modified since last access")
        elif rf.name not in rfs or input(f"{rf.name}" + prompt).lower() == "yes":
            trs = Parser.parse_csv(rf)
            updated_trs[rf.name] = trs
            try:
                rfs[rf.name][0] = rf.stat().st_mtime
            except KeyError:
                rfs[rf.name] = [rf.stat().st_mtime, []]
            update = True
            logging.info(f"{rf.name} parsed")

    if update:
        for rf_name, updated_trs in updated_trs.items():
            filename_set = set(
                (t.date.year, f"{t.date.year}_{t.bank}.csv") for t in updated_trs
            )
            for year, filename in filename_set:
                trs = [t for t in updated_trs if t.date.year == year]
                if filename in dfs.keys():
                    new_trs = [tr for tr in trs if tr not in rfs[rf_name][1]]
                    rem_trs = [tr for tr in rfs[rf_name][1] if tr not in trs]

                    if new_trs:
                        dfs[filename].extend(new_trs).sort()

                    for rem in rem_trs:
                        dfs[filename].remove(rem)

                else:
                    dfs[filename] = trs

                Tr.write_transactions(Path(data_dir) / filename, dfs[filename])
                rfs[rf_name][1] = updated_trs
                logging.debug(f"{filename} written")

        pickle.dump(rfs, open(".raw.pickle", "wb"))
        logging.debug(".raw.pickle written to disk")

    if restart:
        for df in Path(data_dir).iterdir():
            if df.name not in dfs:
                dfs[df.name] = Tr.read_transactions(df)
                for t in dfs[df.name]:
                    t.category = ""

    return dfs


def manual_categorization(trs):
    trs.sort_by_bank()
    for i, transaction in enumerate(trs):
        if not transaction.category:
            category = input(f"{transaction} category: ")
            if category == "stop":
                break
            if category:
                transaction.category = category
                trs[i] = transaction

    trs.sort()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    datafiles = initialize(".raw", "data", restart=False)

    transactions = Transactions()
    for file in datafiles.values():
        transactions.extend(file)
    transactions.sort()

    # reprocess = [Education().name]
    # for i, transaction in enumerate(transactions):
    #     for category in Categories.get_categories():
    #         if transaction.category in reprocess:
    #             transaction.category = ''

    # Categories.categorize(transactions)
    #
    # manual_categorization(transactions)
    #
    # for f, file in datafiles.items():
    #     file_transactions = [t for t in transactions if t in file]
    #     Tr.write_transactions(Path("data") / f, file_transactions)
    #
    Tr.write_transactions("transactions.csv", transactions)

    monthly_transactions = transactions.get_transactions_by_month(
        start=date(2020, 1, 1), end=date(2020, 8, 31)
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

    if False:
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
        plt.legend(loc="upper left")
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
