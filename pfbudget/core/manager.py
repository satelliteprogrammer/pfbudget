import json
from pathlib import Path
import pickle
from typing import Optional
import webbrowser

from pfbudget.common.types import Operation
from pfbudget.db.client import Client
from pfbudget.db.model import (
    Bank,
    BankTransaction,
    Category,
    CategoryGroup,
    CategoryRule,
    CategorySchedule,
    Link,
    MoneyTransaction,
    Nordigen,
    Rule,
    CategorySelector,
    SplitTransaction,
    Tag,
    TagRule,
    Transaction,
    TransactionCategory,
)
from pfbudget.extract.nordigen import NordigenClient, NordigenCredentialsManager
from pfbudget.extract.parsers import parse_data
from pfbudget.extract.psd2 import PSD2Extractor
from pfbudget.load.database import DatabaseLoader
from pfbudget.transform.categorizer import Categorizer
from pfbudget.transform.nullifier import Nullifier
from pfbudget.transform.tagger import Tagger


class Manager:
    def __init__(self, db: str, verbosity: int = 0):
        self._db = db
        self._database: Optional[Client] = None
        self._verbosity = verbosity

    def action(self, op: Operation, params=None):
        if self._verbosity > 0:
            print(f"op={op}, params={params}")

        if params is None:
            params = []

        match (op):
            case Operation.Init:
                pass

            case Operation.Transactions:
                return [t.format for t in self.database.select(Transaction)]

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
                    self.database.insert(sorted(transactions))

            case Operation.Download:
                if params[3]:
                    values = params[3]
                    banks = self.database.select(Bank, lambda: Bank.name.in_(values))
                else:
                    banks = self.database.select(Bank, Bank.nordigen)

                extractor = PSD2Extractor(Manager.nordigen_client())

                transactions = []
                for bank in banks:
                    transactions.extend(extractor.extract(bank, params[0], params[1]))

                # dry-run
                if params[2]:
                    print(sorted(transactions))
                    return

                loader = DatabaseLoader(self.database)
                loader.load(sorted(transactions))

            case Operation.Categorize:
                with self.database.session as session:
                    uncategorized = session.select(
                        BankTransaction, lambda: ~BankTransaction.category.has()
                    )
                    categories = session.select(Category)
                    tags = session.select(Tag)

                    rules = [cat.rules for cat in categories if cat.name == "null"]
                    Nullifier(rules).transform_inplace(uncategorized)

                    rules = [rule for cat in categories for rule in cat.rules]
                    Categorizer(rules).transform_inplace(uncategorized)

                    rules = [rule for tag in tags for rule in tag.rules]
                    Tagger(rules).transform_inplace(uncategorized)

            case Operation.BankMod:
                self.database.update(Bank, params)

            case Operation.PSD2Mod:
                self.database.update(Nordigen, params)

            case Operation.BankDel:
                self.database.delete(Bank, Bank.name, params)

            case Operation.PSD2Del:
                self.database.delete(Nordigen, Nordigen.name, params)

            case Operation.Token:
                Manager.nordigen_client().generate_token()

            case Operation.RequisitionId:
                link, _ = Manager.nordigen_client().requisition(params[0], params[1])
                print(f"Opening {link} to request access to {params[0]}")
                webbrowser.open(link)

            case Operation.PSD2CountryBanks:
                banks = Manager.nordigen_client().country_banks(params[0])
                print(banks)

            case (
                Operation.BankAdd
                | Operation.CategoryAdd
                | Operation.GroupAdd
                | Operation.PSD2Add
                | Operation.RuleAdd
                | Operation.TagAdd
                | Operation.TagRuleAdd
            ):
                self.database.insert(params)

            case Operation.CategoryUpdate:
                self.database.update(Category, params)

            case Operation.CategoryRemove:
                self.database.delete(Category, Category.name, params)

            case Operation.CategorySchedule:
                raise NotImplementedError

            case Operation.RuleRemove:
                self.database.delete(CategoryRule, CategoryRule.id, params)

            case Operation.TagRemove:
                self.database.delete(Tag, Tag.name, params)

            case Operation.TagRuleRemove:
                self.database.delete(TagRule, TagRule.id, params)

            case Operation.RuleModify | Operation.TagRuleModify:
                self.database.update(Rule, params)

            case Operation.GroupRemove:
                self.database.delete(CategoryGroup, CategoryGroup.name, params)

            case Operation.Forge:
                if not (
                    isinstance(params[0], int)
                    and all(isinstance(p, int) for p in params[1])
                ):
                    raise TypeError("f{params} are not transaction ids")

                with self.database.session as session:
                    id = params[0]
                    original = session.select(
                        Transaction, lambda: Transaction.id == id
                    )[0]

                    ids = params[1]
                    links = session.select(Transaction, lambda: Transaction.id.in_(ids))

                    if not original.category:
                        original.category = self.askcategory(original)

                    for link in links:
                        if (
                            not link.category
                            or link.category.name != original.category.name
                        ):
                            print(
                                f"{link} category will change to"
                                f" {original.category.name}"
                            )
                            link.category = original.category

                    tobelinked = [Link(original.id, link.id) for link in links]
                    session.insert(tobelinked)

            case Operation.Dismantle:
                raise NotImplementedError

            case Operation.Split:
                if len(params) < 1 and not all(
                    isinstance(p, Transaction) for p in params
                ):
                    raise TypeError(f"{params} are not transactions")

                # t -> t1, t2, t3; t.value == Σti.value
                original: Transaction = params[0]
                if not original.amount == sum(t.amount for t in params[1:]):
                    raise ValueError(
                        f"{original.amount}€ != {sum(v for v, _ in params[1:])}€"
                    )

                with self.database.session as session:
                    originals = session.select(
                        Transaction, lambda: Transaction.id == original.id
                    )
                    assert len(originals) == 1, ">1 transactions matched {original.id}!"

                    originals[0].split = True
                    transactions = []
                    for t in params[1:]:
                        if originals[0].date != t.date:
                            t.date = originals[0].date
                            print(
                                f"{t.date} is different from original date"
                                f" {originals[0].date}, using original"
                            )

                        splitted = SplitTransaction(
                            t.date, t.description, t.amount, originals[0].id
                        )
                        splitted.category = t.category
                        transactions.append(splitted)

                    session.insert(transactions)

            case Operation.Export:
                self.dump(params[0], params[1], self.database.select(Transaction))

            case Operation.Import:
                transactions = []
                for row in self.load(params[0], params[1]):
                    match row["type"]:
                        case "bank":
                            transaction = BankTransaction(
                                row["date"],
                                row["description"],
                                row["amount"],
                                row["bank"],
                            )

                        case "money":
                            transaction = MoneyTransaction(
                                row["date"], row["description"], row["amount"]
                            )

                        # TODO case "split" how to match to original transaction?? also
                        # save ids?
                        case _:
                            continue

                    if category := row.pop("category", None):
                        transaction.category = TransactionCategory(
                            category["name"], category["selector"]["selector"]
                        )

                    transactions.append(transaction)

                if self.certify(transactions):
                    self.database.insert(transactions)

            case Operation.ExportBanks:
                self.dump(params[0], params[1], self.database.select(Bank))

            case Operation.ImportBanks:
                banks = []
                for row in self.load(params[0], params[1]):
                    bank = Bank(row["name"], row["BIC"], row["type"])
                    if row["nordigen"]:
                        bank.nordigen = Nordigen(**row["nordigen"])
                    banks.append(bank)

                if self.certify(banks):
                    self.database.insert(banks)

            case Operation.ExportCategoryRules:
                self.dump(params[0], params[1], self.database.select(CategoryRule))

            case Operation.ImportCategoryRules:
                rules = [CategoryRule(**row) for row in self.load(params[0], params[1])]

                if self.certify(rules):
                    self.database.insert(rules)

            case Operation.ExportTagRules:
                self.dump(params[0], params[1], self.database.select(TagRule))

            case Operation.ImportTagRules:
                rules = [TagRule(**row) for row in self.load(params[0], params[1])]

                if self.certify(rules):
                    self.database.insert(rules)

            case Operation.ExportCategories:
                self.dump(params[0], params[1], self.database.select(Category))

            case Operation.ImportCategories:
                # rules = [Category(**row) for row in self.load(params[0])]
                categories = []
                for row in self.load(params[0], params[1]):
                    category = Category(row["name"], row["group"])
                    if len(row["rules"]) > 0:
                        # Only category rules could have been created with a rule
                        rules = row["rules"]
                        for rule in rules:
                            del rule["type"]

                        category.rules = [CategoryRule(**rule) for rule in rules]
                    if row["schedule"]:
                        category.schedule = CategorySchedule(**row["schedule"])
                    categories.append(category)

                if self.certify(categories):
                    self.database.insert(categories)

            case Operation.ExportCategoryGroups:
                self.dump(params[0], params[1], self.database.select(CategoryGroup))

            case Operation.ImportCategoryGroups:
                groups = [
                    CategoryGroup(**row) for row in self.load(params[0], params[1])
                ]

                if self.certify(groups):
                    self.database.insert(groups)

    def parse(self, filename: Path, args: dict):
        return parse_data(filename, args)

    def askcategory(self, transaction: Transaction):
        selector = CategorySelector.manual

        categories = self.database.select(Category)

        while True:
            category = input(f"{transaction}: ")
            if category in [c.name for c in categories]:
                return TransactionCategory(category, selector)

    @staticmethod
    def dump(fn, format, sequence):
        if format == "pickle":
            with open(fn, "wb") as f:
                pickle.dump([e.format for e in sequence], f)
        elif format == "json":
            with open(fn, "w", newline="") as f:
                json.dump([e.format for e in sequence], f, indent=4, default=str)
        else:
            print("format not well specified")

    @staticmethod
    def load(fn, format):
        if format == "pickle":
            with open(fn, "rb") as f:
                return pickle.load(f)
        else:
            print("format not well specified")
            return []

    @staticmethod
    def certify(imports: list) -> bool:
        if input(f"{imports[:10]}\nDoes the import seem correct? (y/n)") == "y":
            return True
        return False

    @property
    def database(self) -> Client:
        if not self._database:
            self._database = Client(self._db, echo=self._verbosity > 2)
        return self._database

    @staticmethod
    def nordigen_client() -> NordigenClient:
        return NordigenClient(NordigenCredentialsManager.default)
