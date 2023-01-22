from pathlib import Path
import pickle
import webbrowser

from pfbudget.common.types import Operation
from pfbudget.core.categorizer import Categorizer
from pfbudget.db.client import DbClient
from pfbudget.db.model import (
    Bank,
    BankTransaction,
    Category,
    CategoryGroup,
    CategoryRule,
    CategorySelector,
    Link,
    MoneyTransaction,
    Nordigen,
    Rule,
    Tag,
    TagRule,
    Transaction,
    TransactionCategory,
)
from pfbudget.input.nordigen import NordigenInput
from pfbudget.input.parsers import parse_data


class Manager:
    def __init__(self, db: str, verbosity: int = 0):
        self._db = db
        self._verbosity = verbosity

    def action(self, op: Operation, params: list):
        if self._verbosity > 0:
            print(f"op={op}, params={params}")

        match (op):
            case Operation.Init:
                pass

            case Operation.Parse:
                # Adapter for the parse_data method. Can be refactored.
                args = {"bank": params[1], "creditcard": params[2], "category": None}
                transactions = []
                for path in [Path(p) for p in params[0]]:
                    if path.is_dir():
                        for file in path.iterdir():
                            transactions.extend(self.parse(file, args))
                    elif path.is_file():
                        transactions.extend(self.parse(path, args))
                    else:
                        raise FileNotFoundError(path)

                if (
                    len(transactions) > 0
                    and input(f"{transactions[:5]}\nCommit? (y/n)") == "y"
                ):
                    with self.db.session() as session:
                        session.add(sorted(transactions))

            case Operation.Download:
                client = NordigenInput()
                with self.db.session() as session:
                    if len(params[3]) == 0:
                        client.banks = session.get(Bank, Bank.nordigen)
                    else:
                        client.banks = session.get(Bank, Bank.name, params[3])
                    session.expunge_all()
                client.start = params[0]
                client.end = params[1]
                transactions = client.parse()

                # dry-run
                if not params[2]:
                    with self.db.session() as session:
                        session.add(sorted(transactions))
                else:
                    print(transactions)

            case Operation.Categorize:
                with self.db.session() as session:
                    uncategorized = session.get(
                        BankTransaction, ~BankTransaction.category.has()
                    )
                    categories = session.get(Category)
                    tags = session.get(Tag)
                    Categorizer().rules(uncategorized, categories, tags)

            case Operation.ManualCategorization:
                with self.db.session() as session:
                    uncategorized = session.get(
                        Transaction, ~Transaction.category.has()
                    )
                    categories = session.get(Category)
                    tags = session.get(Tag)
                    Categorizer().manual(uncategorized, categories, tags)

            case Operation.BankMod:
                with self.db.session() as session:
                    session.update(Bank, params)

            case Operation.NordigenMod:
                with self.db.session() as session:
                    session.update(Nordigen, params)

            case Operation.BankDel:
                with self.db.session() as session:
                    session.remove_by_name(Bank, params)

            case Operation.NordigenDel:
                with self.db.session() as session:
                    session.remove_by_name(Nordigen, params)

            case Operation.Token:
                NordigenInput().token()

            case Operation.RequisitionId:
                link, _ = NordigenInput().requisition(params[0], params[1])
                print(f"Opening {link} to request access to {params[0]}")
                webbrowser.open(link)

            case Operation.NordigenCountryBanks:
                banks = NordigenInput().country_banks(params[0])
                print(banks)

            case Operation.BankAdd | Operation.CategoryAdd | Operation.NordigenAdd | Operation.RuleAdd | Operation.TagAdd | Operation.TagRuleAdd:
                with self.db.session() as session:
                    session.add(params)

            case Operation.CategoryUpdate:
                with self.db.session() as session:
                    session.updategroup(*params)

            case Operation.CategoryRemove:
                with self.db.session() as session:
                    session.remove_by_name(Category, params)

            case Operation.CategorySchedule:
                with self.db.session() as session:
                    session.updateschedules(params)

            case Operation.RuleRemove:
                assert all(isinstance(param, int) for param in params)
                with self.db.session() as session:
                    session.remove_by_id(CategoryRule, params)

            case Operation.TagRemove:
                with self.db.session() as session:
                    session.remove_by_name(Tag, params)

            case Operation.TagRuleRemove:
                assert all(isinstance(param, int) for param in params)
                with self.db.session() as session:
                    session.remove_by_id(TagRule, params)

            case Operation.RuleModify | Operation.TagRuleModify:
                assert all(isinstance(param, dict) for param in params)
                with self.db.session() as session:
                    session.update(Rule, params)

            case Operation.GroupAdd:
                with self.db.session() as session:
                    session.add(params)

            case Operation.GroupRemove:
                assert all(isinstance(param, CategoryGroup) for param in params)
                with self.db.session() as session:
                    session.remove_by_name(CategoryGroup, params)

            case Operation.Forge:
                with self.db.session() as session:
                    session.add(params)

            case Operation.Dismantle:
                assert all(isinstance(param, Link) for param in params)

                with self.db.session() as session:
                    original = params[0].original
                    links = [link.link for link in params]
                    session.remove_links(original, links)

            case Operation.Export:
                with self.db.session() as session:
                    self.dump(params[0], sorted(session.get(Transaction)))

            case Operation.Import:
                transactions = []
                for row in self.load(params[0]):
                    match row["type"]:
                        case "bank":
                            transaction = BankTransaction(
                                row["date"],
                                row["description"],
                                row["amount"],
                                row["bank"],
                                False,
                            )

                        case "money":
                            transaction = MoneyTransaction(
                                row["date"], row["description"], row["amount"], False
                            )

                        # TODO case "split" how to match to original transaction?? also save ids?
                        case _:
                            continue

                    if category := row.pop("category", None):
                        transaction.category = TransactionCategory(
                            category["name"],
                            CategorySelector(category["selector"]["selector"]),
                        )

                    transactions.append(transaction)

                if (
                    len(transactions) > 0
                    and input(
                        f"{transactions[:5]}\nDoes the import seem correct? (y/n)"
                    )
                    == "y"
                ):
                    with self.db.session() as session:
                        session.add(transactions)

            case Operation.ExportCategoryRules:
                with self.db.session() as session:
                    self.dump(params[0], session.get(CategoryRule))

            case Operation.ImportCategoryRules:
                rules = [CategoryRule(**row) for row in self.load(params[0])]

                if (
                    len(rules) > 0
                    and input(f"{rules[:5]}\nDoes the import seem correct? (y/n)")
                    == "y"
                ):
                    with self.db.session() as session:
                        session.add(rules)

            case Operation.ExportTagRules:
                with self.db.session() as session:
                    self.dump(params[0], session.get(TagRule))

            case Operation.ImportTagRules:
                rules = [TagRule(**row) for row in self.load(params[0])]

                if (
                    len(rules) > 0
                    and input(f"{rules[:5]}\nDoes the import seem correct? (y/n)")
                    == "y"
                ):
                    with self.db.session() as session:
                        session.add(rules)

    def parse(self, filename: Path, args: dict):
        return parse_data(filename, args)

    def dump(self, fn, sequence):
        with open(fn, "wb") as f:
            pickle.dump([e.format for e in sequence], f)

    def load(self, fn):
        with open(fn, "rb") as f:
            return pickle.load(f)

    @property
    def db(self) -> DbClient:
        return DbClient(self._db, self._verbosity > 2)

    @db.setter
    def db(self, url: str):
        self._db = url
