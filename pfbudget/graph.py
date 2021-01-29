from dateutil.rrule import MONTHLY, YEARLY
import matplotlib.pyplot as plt

from .categories import (
    get_income_categories,
    get_fixed_expenses,
    get_required_expenses,
    get_discretionary_expenses,
)
from .transactions import load_transactions, daterange, by_category, by_month


def monthly(state, start, end):
    transactions = load_transactions(state.data_dir)

    monthly_transactions = by_month(transactions, start, end)
    monthly_transactions_by_categories = {}
    income, fixed, required, discretionary = [], [], [], []

    for month, transactions in monthly_transactions.items():
        monthly_transactions_by_categories[month] = by_category(transactions)
        income.append(
            sum(
                float(t.value)
                for category, transactions in monthly_transactions_by_categories[
                    month
                ].items()
                if transactions and category in get_income_categories()
                for t in transactions
            )
        )
        fixed.append(
            sum(
                -float(t.value)
                for category, transactions in monthly_transactions_by_categories[
                    month
                ].items()
                if transactions and category in get_fixed_expenses()
                for t in transactions
            )
        )
        required.append(
            sum(
                -float(t.value)
                for category, transactions in monthly_transactions_by_categories[
                    month
                ].items()
                if transactions and category in get_required_expenses()
                for t in transactions
            )
        )
        discretionary.append(
            sum(
                -float(t.value)
                for category, transactions in monthly_transactions_by_categories[
                    month
                ].items()
                if transactions and category in get_discretionary_expenses()
                for t in transactions
            )
        )

    plt.plot(daterange(start, end, "month"), income, label="Income")
    plt.stackplot(
        daterange(start, end, "month"),
        fixed,
        required,
        discretionary,
        labels=["Fixed", "Required", "Discretionary"],
    )
    plt.legend(loc="upper left")
    plt.show()
