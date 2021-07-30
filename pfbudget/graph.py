from __future__ import annotations
from calendar import monthrange
from dateutil.rrule import rrule, MONTHLY
from typing import TYPE_CHECKING
import datetime as dt
import matplotlib.pyplot as plt

import pfbudget.categories


if TYPE_CHECKING:
    from pfbudget.database import DBManager


def monthly(
    db: DBManager, args: dict, start: dt.date = dt.date.min, end: dt.date = dt.date.max
):
    transactions = db.get_daterange(start, end)
    start, end = transactions[0].date, transactions[-1].date
    monthly_transactions = tuple(
        (
            month,
            {
                group: sum(
                    transaction.value
                    for transaction in transactions
                    if transaction.category in categories
                    and month
                    <= transaction.date
                    <= month
                    + dt.timedelta(days=monthrange(month.year, month.month)[1] - 1)
                )
                for group, categories in pfbudget.categories.groups.items()
            },
        )
        for month in [
            month.date()
            for month in rrule(
                MONTHLY, dtstart=start.replace(day=1), until=end.replace(day=1)
            )
        ]
    )

    plt.figure(tight_layout=True)
    plt.plot(
        list(rrule(MONTHLY, dtstart=start.replace(day=1), until=end.replace(day=1))),
        [groups["income"] for _, groups in monthly_transactions],
    )
    plt.stackplot(
        list(rrule(MONTHLY, dtstart=start.replace(day=1), until=end.replace(day=1))),
        [
            [-groups[group] for _, groups in monthly_transactions]
            for group in pfbudget.categories.groups
            if group != "income" and group != "investment"
        ],
        labels=[
            group
            for group in pfbudget.categories.groups
            if group != "income" and group != "investment"
        ],
    )
    plt.legend(loc="upper left")
    if args["save"]:
        plt.savefig("graph.png")
    else:
        plt.show()


def discrete(
    db: DBManager, args: dict, start: dt.date = dt.date.min, end: dt.date = dt.date.max
):
    transactions = db.get_daterange(start, end)
    start, end = transactions[0].date, transactions[-1].date
    monthly_transactions = tuple(
        (
            month,
            {
                category: sum(
                    transaction.value
                    for transaction in transactions
                    if transaction.category == category
                    and month
                    <= transaction.date
                    <= month
                    + dt.timedelta(days=monthrange(month.year, month.month)[1] - 1)
                )
                for category in pfbudget.categories.categories
            },
        )
        for month in [
            month.date()
            for month in rrule(
                MONTHLY, dtstart=start.replace(day=1), until=end.replace(day=1)
            )
        ]
    )

    plt.figure(figsize=(30, 10))
    plt.plot(
        list(rrule(MONTHLY, dtstart=start.replace(day=1), until=end.replace(day=1))),
        [
            sum(
                value
                for category, value in categories.items()
                if category in pfbudget.categories.groups["income"]
            )
            for _, categories in monthly_transactions
        ],
    )
    plt.stackplot(
        list(rrule(MONTHLY, dtstart=start.replace(day=1), until=end.replace(day=1))),
        [
            [-categories[category] for _, categories in monthly_transactions]
            for category in pfbudget.categories.categories
            if category not in pfbudget.categories.groups["income"]
            and category not in pfbudget.categories.groups["investment"]
        ],
        labels=[
            category
            for category in pfbudget.categories.categories
            if category not in pfbudget.categories.groups["income"]
            and category not in pfbudget.categories.groups["investment"]
        ],
    )
    plt.legend(loc="upper left")
    plt.tight_layout()
    if args["save"]:
        plt.savefig("graph.png")
    else:
        plt.show()
