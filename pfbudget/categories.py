from collections import namedtuple
import datetime as dt
import logging
import re
import yaml

from .database import DBManager


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
    transactions = [list(t) for t in db.get_uncategorized_transactions()]
    for transaction in transactions:
        if not transaction[4]:
            for name, category in categories.items():
                if matches(transaction, category):
                    transaction[4] = name
                    break
    db.update_categories(transactions)

    # 4th) Manually update categories from the uncategorized transactions
    transactions = [list(t) for t in db.get_uncategorized_transactions()]
    if transactions:
        print(f"Still {len(transactions)} uncategorized transactions left")
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
                    transaction[4] = category
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

            not_vacations = categories["Travel"].negative_regex

            if transactions := [
                list(t) for t in db.get_daterage_without(start, end, *not_vacations)
            ]:
                for transaction in transactions:
                    transaction[4] = "Travel"

                db.update_categories(transactions)

    except KeyError as e:
        print(e)


def nulls(db: DBManager) -> None:
    null = categories.get("Null", Options())
    transactions = [list(t) for t in db.get_uncategorized_transactions()]
    matching_transactions = []
    for t in transactions:
        for cancel in (
            cancel
            for cancel in transactions
            if (
                dt.datetime.fromisoformat(t[0]) - dt.timedelta(days=null.timedelta)
                <= dt.datetime.fromisoformat(cancel[0])
                and dt.datetime.fromisoformat(cancel[0])
                <= dt.datetime.fromisoformat(t[0]) + dt.timedelta(days=null.timedelta)
                and (matches(t, null) if null.regex else True)
                and t[2] != cancel[2]
                and t not in matching_transactions
                and cancel not in matching_transactions
                and cancel != t
                and t[3] == -cancel[3]
            )
        ):
            t[4] = "Null"
            cancel[4] = "Null"
            matching_transactions.extend([t, cancel])
            break  # There will only be one match per null transaction pair

    db.update_categories(matching_transactions)


def matches(transaction, category: Options):
    if not category.regex:
        return False
    return any(
        re.compile(pattern).search(transaction[1].lower()) for pattern in category.regex
    )
