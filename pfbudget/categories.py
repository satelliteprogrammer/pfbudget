from datetime import date, timedelta
from re import compile as c


class Categories:
    name = ""
    regex = []
    banks = []
    values = []
    range = ()

    def search(self, t):
        if not self.regex:
            return False

        if self.banks:
            return any(
                pattern.search(t.description.lower())
                for pattern in self.regex
                if t.bank in self.banks
            )
        elif self.range:
            return any(
                pattern.search(t.description.lower())
                for pattern in self.regex
                if self.range[0] < t.value < self.range[1]
            )
        elif self.values:
            return any(
                pattern.search(t.description.lower())
                for pattern in self.regex
                if t.value in self.values
            )
        else:
            return any(pattern.search(t.description.lower()) for pattern in self.regex)

    @classmethod
    def get_categories(cls):
        return cls.__subclasses__()

    @classmethod
    def get_categories_names(cls):
        return [cat.name for cat in cls.get_categories()]

    @classmethod
    def get_income_categories(cls):
        return [cat.name for cat in cls.get_categories() if "Income" in cat.name]

    @classmethod
    def get_fixed_expenses(cls):
        return [
            Utilities.name,
            Commute.name,
        ]

    @classmethod
    def get_variable_expenses(cls):
        return [Groceries.name]

    @classmethod
    def get_discretionary_expenses(cls):
        return [
            cat.name
            for cat in cls.get_categories()
            if cat.name
            not in [
                *cls.get_income_categories(),
                *cls.get_fixed_expenses(),
                *cls.get_variable_expenses(),
                Investment.name,
                Null.name,
            ]
        ]


class Income1(Categories):
    name = "Income1"
    regex = [c("company A")]


class Income2(Categories):
    name = "Income2"
    regex = [c("transfer")]
    banks = ["BankA"]


class Income3(Categories):
    name = "Income3"
    regex = [c("company B")]


class Null(Categories):
    name = "Null"
    regex = [
        c("transfer A to B"),
        c("1"),
        c("2"),
    ]

    def search(self, transaction):
        pass

    def search_all(self, transactions):
        matches = []
        for transaction in transactions:
            for cancel in [
                cancel
                for cancel in transactions
                if (
                    transaction.date - timedelta(days=4)
                    <= cancel.date
                    <= transaction.date + timedelta(days=4)
                    and any(
                        pattern.search(transaction.description.lower())
                        for pattern in self.regex
                    )
                    and transaction.bank != cancel.bank
                    and transaction
                    and cancel not in matches
                    and cancel != transaction
                )
            ]:

                if transaction.value == -cancel.value:
                    matches.extend([transaction, cancel])
                    # if transaction.value > 0:
                    #     transaction, cancel = cancel, transaction
                    # print('{} -> {}'.format(transaction, cancel))
                    break

        return matches


class Commute(Categories):
    name = "Commute"
    regex = [c("uber"), c("train")]
    values = [-50]

    def search(self, t):
        if any(pattern.search(t.description.lower()) for pattern in self.regex[:1]):
            return True
        elif t.value in self.values:
            return any(
                pattern.search(t.description.lower()) for pattern in self.regex[1:]
            )
        else:
            return False


class Utilities(Categories):
    name = "Utilities"
    regex = [c("electricity", "water", "internet")]
    values = [-35]

    def search(self, t):
        if any(pattern.search(t.description.lower()) for pattern in self.regex[:2]):
            return True
        elif t.value in self.values:
            return any(
                pattern.search(t.description.lower()) for pattern in self.regex[2:]
            )
        else:
            return False


class Groceries(Categories):
    name = "Groceries"
    regex = [
        c("lidl"),
        c("e.leclerc"),
        c("aldi"),
    ]


class EatingOut(Categories):
    name = "Eating Out"
    regex = [
        c("restaurant 1"),
        c("restaurant 2"),
    ]


class Entertainment(Categories):
    name = "Entertainment"
    regex = [c("cinema"), c("steam")]


class Pets(Categories):
    name = "Pets"


class Travel(Categories):
    name = "Travel"
    regex = [c("ryanair"), c("easyjet"), c("airbnb")]
    not_in_travel = [
        *Categories.get_income_categories(),
        Utilities.name,
    ]

    @staticmethod
    def search_all(transactions, start, end):
        matches = []
        for transaction in transactions:
            if start <= transaction.date < end:
                matches.append(transaction)

        return matches


class Miscellaneous(Categories):
    name = "Miscellaneous"


class Investment(Categories):
    name = "Investment"
    regex = [c("subscrition")]
    banks = ["BankC"]
