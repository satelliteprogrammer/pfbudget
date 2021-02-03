from dateutil.rrule import MONTHLY, YEARLY
import matplotlib.pyplot as plt

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
)


def monthly(state, start, end):
    transactions = load_transactions(state.data_dir)
    if not start:
        start = transactions[0].date
    if not end:
        end = transactions[-1].date

    income, fixed, required, health, discretionary = [], [], [], [], []
    monthly_transactions_by_categories = by_month_and_category(transactions, start, end)

    for _, transactions_by_category in monthly_transactions_by_categories.items():
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

    plt.plot(daterange(start, end, "month"), income, label="Income")
    plt.stackplot(
        daterange(start, end, "month"),
        fixed,
        required,
        health,
        discretionary,
        labels=["Fixed", "Required", "Health", "Discretionary"],
    )
    plt.legend(loc="upper left")
    plt.show()


def discrete(state, start, end):
    transactions = load_transactions(state.data_dir)
    if not start:
        start = transactions[0].date
    if not end:
        end = transactions[-1].date

    income, fixed, required, health, discretionary = [], [], [], [], []
    monthly_transactions_by_categories = by_month_and_category(transactions, start, end)

    for _, transactions_by_category in monthly_transactions_by_categories.items():
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
        d = []
        for category, transactions in transactions_by_category.items():
            if category in get_discretionary_expenses():
                try:
                    d.append(sum(-float(t.value) for t in transactions))
                except TypeError:
                    d.append(0)

        discretionary.append(d)

    # transposing discretionary
    discretionary = list(map(list, zip(*discretionary)))

    plt.plot(daterange(start, end, "month"), income, label="Income")
    plt.stackplot(
        daterange(start, end, "month"),
        fixed,
        required,
        health,
        *discretionary,
        labels=["Fixed", "Required", "Health", *get_discretionary_expenses()],
    )
    plt.legend(loc="upper left")
    plt.grid()
    plt.show()


def average(state, start, end):
    transactions = load_transactions(state.data_dir)

    income, fixed, required, health, discretionary = [], [], [], [], []
    monthly_transactions_by_categories = by_month_and_category(transactions, start, end)

    for _, transactions_by_category in monthly_transactions_by_categories.items():
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
        d = []
        for category, transactions in transactions_by_category.items():
            if category in get_discretionary_expenses():
                try:
                    d.append(sum(-float(t.value) for t in transactions))
                except TypeError:
                    d.append(0)

        discretionary.append(d)

    # transposing discretionary
    discretionary = list(map(list, zip(*discretionary)))

    print(discretionary)

    n = len(daterange(start, end, "month"))

    avg_income = sum(income) / n

    l_avg_income = [avg_income] * n

    avg_fixed = [sum(fixed) / n] * n
    avg_required = [sum(required) / n] * n
    avg_health = [sum(health) / n] * n
    avg_discretionary = [[sum(d) / n] * n for d in discretionary]

    print(avg_discretionary)

    plt.plot(daterange(start, end, "month"), l_avg_income, label=f"Income {avg_income}")
    plt.stackplot(
        daterange(start, end, "month"),
        avg_fixed,
        avg_required,
        avg_health,
        *avg_discretionary,
        labels=[
            f"Fixed {avg_fixed[0]/avg_income * 100}%",
            f"Required {avg_required[0]/avg_income * 100}%",
            f"Health {avg_health[0]/avg_income * 100}%",
            *[
                f"{e} {avg_discretionary[i][0]/avg_income * 100}%"
                for i, e in enumerate(get_discretionary_expenses())
            ],
        ],
    )
    plt.legend(bbox_to_anchor=(1, 1), loc="upper left")
    plt.show()
