from .categories import (
    get_income_categories,
    get_fixed_expenses,
    get_required_expenses,
    get_health_expenses,
    get_discretionary_expenses,
)
from .transactions import (
    load_transactions,
    daterange,
    by_category,
    by_month,
    by_month_and_category,
    by_year_and_category,
)


def net(state, start=None, end=None):
    transactions = load_transactions(state.data_dir)
    if not start:
        start = transactions[0].date
    if not end:
        end = transactions[-1].date

    income, fixed, required, health, discretionary = [], [], [], [], []
    yearly_transactions_by_categories = by_year_and_category(transactions, start, end)
    for _, transactions_by_category in yearly_transactions_by_categories.items():
        income.append(
            sum(
                float(t.value)
                for category, transactions in transactions_by_category.items()
                if transactions and category in get_income_categories()
                for t in transactions
            )
        )
        fixed.append(
            sum(
                -float(t.value)
                for category, transactions in transactions_by_category.items()
                if transactions and category in get_fixed_expenses()
                for t in transactions
            )
        )
        required.append(
            sum(
                -float(t.value)
                for category, transactions in transactions_by_category.items()
                if transactions and category in get_required_expenses()
                for t in transactions
            )
        )
        health.append(
            sum(
                -float(t.value)
                for category, transactions in transactions_by_category.items()
                if transactions and category in get_health_expenses()
                for t in transactions
            )
        )
        discretionary.append(
            sum(
                -float(t.value)
                for category, transactions in transactions_by_category.items()
                if transactions and category in get_discretionary_expenses()
                for t in transactions
            )
        )

    for i, year in enumerate(yearly_transactions_by_categories.keys()):
        print(year)
        print(
            "Income: {:.2f}, Expenses: {:.2f}, Net: {:.2f}\n"
            "Fixed Expenses: {:.2f}\n"
            "Required Expenses: {:.2f}\n"
            "Health Expenses: {:.2f}\n"
            "Discretionary Expenses: {:.2f}\n".format(
                income[i],
                fixed[i] + required[i] + health[i] + discretionary[i],
                income[i] - (fixed[i] + required[i] + health[i] + discretionary[i]),
                fixed[i],
                required[i],
                health[i],
                discretionary[i],
            )
        )
