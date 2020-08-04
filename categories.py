from datetime import date, timedelta
from re import compile as c


class Categories:
    name = ""
    regex = []
    banks = []
    values = []
    range = ()

    def search(self, t):
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
    def categorize(cls, transactions):

        income_categories = [
            Income1().name,
            Income2().name,
            Income3().name,
        ]

        null_matches = Null().search_all(transactions)
        travel_matches = Travel().search_all(
            transactions, date(2019, 12, 23), date(2020, 1, 2)
        )

        for i, transaction in enumerate(transactions):
            for category in cls.get_categories():
                if category.search(transaction):
                    if not transaction.category:
                        transaction.category = category.name
                        transactions[i] = transaction
                    elif (
                        transaction.category != category.name
                        and transaction.category != Travel().name
                    ):
                        new_category = input(
                            f"{transaction} already has a {transaction.category} assigned. Would you like "
                            f"to change it to {category.name}? (Y/N) "
                        )
                        correct_answer = False
                        while not correct_answer:
                            if new_category.lower() == "y":
                                transaction.category = category.name
                                transactions[i] = transaction
                                correct_answer = True
                            elif new_category.lower() == "n":
                                correct_answer = True
                            else:
                                new_category = input("? ")

            if transaction in travel_matches and transaction.category not in [
                *income_categories,
            ]:
                transaction.category = Travel().name
            if transaction in null_matches:
                transaction.category = Null().name

    @classmethod
    def get_categories(cls):
        return [category() for category in cls.__subclasses__()]


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
