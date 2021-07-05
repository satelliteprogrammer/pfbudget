from __future__ import annotations
from dateutil.rrule import rrule, YEARLY
from typing import TYPE_CHECKING
import datetime as dt

import pfbudget.categories as categories

if TYPE_CHECKING:
    from pfbudget.database import DBManager


def net(db: DBManager, start: dt.date = dt.date.min, end: dt.date = dt.date.max):
    transactions = db.get_daterange(start, end)
    start, end = transactions[0].date, transactions[-1].date

    yearly_transactions = tuple(
        (
            year,
            {
                group: sum(
                    transaction.value
                    for transaction in transactions
                    if transaction.category in categories
                    and year <= transaction.date <= year.replace(month=12, day=31)
                )
                for group, categories in categories.groups.items()
            },
        )
        for year in [
            year.date()
            for year in rrule(
                YEARLY, dtstart=start.replace(day=1), until=end.replace(day=1)
            )
        ]
    )

    for year, groups in yearly_transactions:
        print(year.year)
        print(f"Income: {groups.pop('income'):.2f}€")
        for group, value in groups.items():
            print(f"{group.capitalize()} expenses: {value:.2f}€")
        print()
