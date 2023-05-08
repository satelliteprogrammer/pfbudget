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

        with self.manager.db.session() as session:
            self.categories = session.get(Category)
            self.tags = session.get(Tag)
            session.expunge_all()

    def intro(self) -> None:
        print(
            f"Welcome! Available categories are {[c.name for c in self.categories]} and"
            f" currently existing tags are {[t.name for t in self.tags]}"
        )

    def start(self) -> None:
        self.intro()

        with self.manager.db.session() as session:
            uncategorized = session.uncategorized()
            n = len(uncategorized)
            print(f"{n} left to categorize")

            i = 0
            new = []
            next = uncategorized[i]
            print(next)
            while (command := input("$ ")) != "quit":
                match command:
                    case "help":
                        print(self.help)

                    case "skip":
                        i += 1

                    case "quit":
                        break

                    case "split":
                        new = self.split(next)
                        session.insert(new)

                    case other:
                        if not other:
                            print(self.help)
                            continue

                        if other.startswith("note:"):
                            # TODO adding notes to a splitted transaction won't allow
                            # categorization
                            next.note = Note(other[len("note:") :].strip())
                        else:
                            ct = other.split(":")
                            if (category := ct[0]) not in [
                                c.name for c in self.categories
                            ]:
                                print(self.help, self.categories)

                            tags = []
                            if len(ct) > 1:
                                tags = ct[1:]

                            next.category = TransactionCategory(category, self.selector)
                            for tag in tags:
                                if tag not in [t.name for t in self.tags]:
                                    session.insert([Tag(tag)])
                                    self.tags = session.get(Tag)

                                next.tags.add(TransactionTag(tag))

                            i += 1

                        session.commit()

                next = uncategorized[i] if len(new) == 0 else new.pop()
                print(next)

    def split(self, original: Transaction) -> list[SplitTransaction]:
        total = original.amount
        new = []

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
                    original.date, original.description, amount, original.id
                )
            )

        return new
