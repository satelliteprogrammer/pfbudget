from __future__ import annotations
from collections import namedtuple
from typing import TYPE_CHECKING
import datetime as dt
import logging
import re
import yaml


if TYPE_CHECKING:
    from pfbudget.database import DBManager
    from pfbudget.transactions import Transaction


Options = namedtuple(
    "Options",
    [
        "regex",
        "banks",
        "regular",
        "negative_regex",
        "date_fmt",
        "vacations",
        "timedelta",
    ],
    defaults=[[], [], [], [], "", [], 4],
)

cfg = yaml.safe_load(open("categories.yaml"))
categories = {k: Options(**v) if v else Options() for k, v in cfg.items()}


def categorize_data(db: DBManager):

    # 1st) Classifying null transactions, i.e. transfers between banks.
    # Will not overwrite previous categories
    nulls(db)

    # 2nd) Classifying all vacations by vacation dates
    # Will not overwrite previous categories
    vacations(db)

    # 3rd) Classify all else based on regex
    if transactions := db.get_uncategorized_transactions():
        for transaction in transactions:
            if not transaction.category:
                for name, category in categories.items():
                    if matches(transaction, category):
                        transaction.category = name
                        break
        db.update_categories(
            [transaction for transaction in transactions if transaction.category]
        )

    # 4th) Manually update categories from the uncategorized transactions
    if transactions := db.get_uncategorized_transactions():
        print(
            f"Still {len(transactions)} uncategorized transactions left. Type quit/exit to exit the program."
        )
        for transaction in transactions:
            while True:
                category = input(f"{transaction} category: ")
                if category == "quit" or category == "exit":
                    return
                if category not in categories:
                    print(
                        f"Category {category} doesn't exist. Please use one of {categories.keys()}"
                    )
                else:
                    transaction.category = category
                    db.update_category(transaction)
                    break


def vacations(db: DBManager) -> None:
    try:
        date_fmt = categories["Travel"].date_fmt
        for start, end in categories["Travel"].vacations:
            try:
                start = dt.datetime.strptime(start, date_fmt).date().isoformat()
                end = dt.datetime.strptime(end, date_fmt).date().isoformat()
            except ValueError as e:
                logging.warning(f"{e} continuing...")
                continue

            not_vacations = categories["Travel"].negative_regex  # default is []

            if transactions := db.get_daterange_uncategorized_transactions(start, end):
                for transaction in transactions:
                    if not_vacations:
                        for category in not_vacations:
                            if not matches(
                                transaction, categories.get(category, Options())
                            ):
                                transaction.category = "Travel"
                    else:
                        transaction.category = "Travel"

                db.update_categories(transactions)

    except KeyError as e:
        print(e)


def nulls(db: DBManager) -> None:
    null = categories.get("Null", Options())
    transactions = db.get_uncategorized_transactions()
    if not transactions:
        return

    matching_transactions = []
    for t in transactions:
        for cancel in (
            cancel
            for cancel in transactions
            if (
                t.date - dt.timedelta(days=null.timedelta)
                <= cancel.date
                <= t.date + dt.timedelta(days=null.timedelta)
                and (matches(t, null) if null.regex else True)
                and t.bank != cancel.bank
                and t not in matching_transactions
                and cancel not in matching_transactions
                and cancel != t
                and t.value == -cancel.value
            )
        ):
            t.category = "Null"
            cancel.category = "Null"
            matching_transactions.extend([t, cancel])
            break  # There will only be one match per null transaction pair

    if matching_transactions:
        db.update_categories(matching_transactions)


def matches(transaction: Transaction, category: Options):
    if not category.regex:
        return False
    return any(
        re.compile(pattern).search(transaction.description.lower())
        for pattern in category.regex
    )
