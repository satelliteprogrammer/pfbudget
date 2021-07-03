from __future__ import annotations
from calendar import monthrange
from dateutil.rrule import rrule, MONTHLY
from typing import TYPE_CHECKING
import datetime as dt
import matplotlib.pyplot as plt

import pfbudget.categories as categories

if TYPE_CHECKING:
    from pfbudget.database import DBManager


def monthly(db: DBManager, start: dt.date = dt.date.min, end: dt.date = dt.date.max):
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
                for group, categories in categories.groups.items()
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
        [groups["income"] for _, groups in monthly_transactions],
    )
    plt.stackplot(
        list(rrule(MONTHLY, dtstart=start.replace(day=1), until=end.replace(day=1))),
        [
            [-groups[group] for _, groups in monthly_transactions]
            for group in categories.groups.keys()
            if group != "income"
        ],
        labels=[group for group in categories.groups.keys() if group != "income"],
    )
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig("graph.png")


def discrete(db: DBManager, start: dt.date = dt.date.min, end: dt.date = dt.date.max):
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
                for category in categories.categories.keys()
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
    plt.stackplot(
        list(rrule(MONTHLY, dtstart=start.replace(day=1), until=end.replace(day=1))),
        [
            [-categories[category] for _, categories in monthly_transactions]
            for category in categories.categories.keys()
        ],
        labels=[category for category in categories.categories.keys()],
    )
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig("graph.png")
