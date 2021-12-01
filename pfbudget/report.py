from __future__ import annotations
from dateutil.rrule import rrule, YEARLY
from typing import TYPE_CHECKING
import datetime as dt

import pfbudget.categories

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
                for group, categories in pfbudget.categories.groups.items()
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
        print(f"\n{year.year}\n")

        income = groups.pop("income-fixed") + groups.pop("income-extra")
        print(f"Income: {income:.2f} €\n")

        investments = -groups.pop("investment")

        expenses = 0
        for group, value in groups.items():
            expenses -= value
            if income != 0:
                print(
                    f"{group.capitalize()} expenses: {-value:.2f} € ({-value/income*100:.1f}%)"
                )
            else:
                print(f"{group.capitalize()} expenses: {-value:.2f} €")

        print(f"\nNet total: {income-expenses:.2f} €")
        if income != 0:
            print(
                f"Total expenses are {expenses:.2f} ({expenses/income*100:.1f}% of income)\n"
            )
        else:
            print(f"Total expenses are {expenses:.2f}. No income this year!\n")

        print(f"Invested: {investments:.2f}€\n")
