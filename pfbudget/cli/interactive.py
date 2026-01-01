import decimal

from ..core.manager import Manager
from ..db.model import (
    Category,
    Note,
    CategorySelector,
    SplitTransaction,
    Tag,
    Transaction,
    TransactionCategory,
    TransactionTag,
)


class Interactive:
    help = "category(:tag)/split/note:/skip/quit"
    selector = CategorySelector.manual

    def __init__(self, manager: Manager) -> None:
        self.manager = manager

        self.categories = self.manager.database.select(Category)
        self.tags = self.manager.database.select(Tag)

    def intro(self) -> None:
        print(
            f"Welcome! Available categories are {[c.name for c in self.categories]} and"
            f" currently existing tags are {[t.name for t in self.tags]}"
        )

    def start(self) -> None:
        self.intro()

        with self.manager.database.session as session:
            uncategorized = session.select(
                Transaction, lambda: ~Transaction.category.has()
            )
            list(uncategorized).sort()
            n = len(uncategorized)
            print(f"{n} left to categorize")

            i = 0
            new = []

            while i < len(uncategorized):
                current = uncategorized[i] if len(new) == 0 else new.pop()
                print(current)
                command = input("$ ")

                match command:
                    case "help":
                        print(self.help)

                    case "skip":
                        i += 1

                    case "quit":
                        break

                    case "split":
                        new = self.split(current)
                        session.insert(new)

                    case other:
                        if not other:
                            print(self.help)
                            continue

                        if other.startswith("note:"):
                            # TODO adding notes to a splitted transaction won't allow
                            # categorization
                            current.note = Note(other[len("note:") :].strip())
                        else:
                            ct = other.split(":")
                            if (category := ct[0]) not in [
                                c.name for c in self.categories
                            ]:
                                print(self.help, self.categories)
                                continue

                            tags = []
                            if len(ct) > 1:
                                tags = ct[1:]

                            current.category = TransactionCategory(
                                category, self.selector
                            )
                            for tag in tags:
                                if tag not in [t.name for t in self.tags]:
                                    session.insert([Tag(tag)])
                                    self.tags = session.select(Tag)

                                current.tags.add(TransactionTag(tag))

                            if len(new) == 0:
                                i += 1

    def split(self, original: Transaction) -> list[SplitTransaction]:
        total = original.amount
        new: list[SplitTransaction] = []

        done = False
        while not done:
            if abs(sum(t.amount for t in new)) > abs(total):
                print("Overflow, try again")
                new.clear()
                continue

            if sum(t.amount for t in new) == total:
                done = True
                break

            amount = decimal.Decimal(input("amount: "))
            new.append(
                SplitTransaction(
                    original.date, original.description, amount, original=original.id
                )
            )

        return new
