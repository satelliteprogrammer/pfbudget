import csv
from pathlib import Path
import pickle
import webbrowser

from pfbudget.common.types import Operation
from pfbudget.db.client import DbClient
from pfbudget.db.model import (
    Bank,
    BankTransaction,
    Category,
    CategoryGroup,
    CategoryRule,
    CategorySchedule,
    CategorySelector,
    Link,
    MoneyTransaction,
    Nordigen,
    Rule,
    Selector_T,
    SplitTransaction,
    Tag,
    TagRule,
    Transaction,
    TransactionCategory,
)
from pfbudget.extract.nordigen import NordigenClient, NordigenCredentialsManager
from pfbudget.extract.parsers import parse_data
from pfbudget.extract.psd2 import PSD2Extractor
from pfbudget.transform.categorizer import Categorizer
from pfbudget.transform.nullifier import Nullifier


class Manager:
    def __init__(self, db: str, verbosity: int = 0):
        self._db = db
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
                with self.db.session() as session:
                    transactions = session.get(Transaction)
                    ret = [t.format for t in transactions]
                return ret

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
                client = Manager.nordigen_client()
                with self.db.session() as session:
                    if len(params[3]) == 0:
                        banks = session.get(Bank, Bank.nordigen)
                    else:
                        banks = session.get(Bank, Bank.name, params[3])
                    session.expunge_all()

                extractor = PSD2Extractor(client)
                transactions = []
                for bank in banks:
                    transactions.extend(extractor.extract(bank, params[0], params[1]))

                # dry-run
                if not params[2]:
                    with self.db.session() as session:
                        session.add(sorted(transactions))
                else:
                    print(sorted(transactions))

            case Operation.Categorize:
                with self.db.session() as session:
                    uncategorized = session.get(
                        BankTransaction, ~BankTransaction.category.has()
                    )
                    categories = session.get(Category)
                    tags = session.get(Tag)

                    null_rules = [cat.rules for cat in categories if cat.name == "null"]
                    Nullifier(null_rules).transform_inplace(uncategorized)

                    Categorizer().rules(uncategorized, categories, tags, params[0])

            case Operation.BankMod:
                with self.db.session() as session:
                    session.update(Bank, params)

            case Operation.PSD2Mod:
                with self.db.session() as session:
                    session.update(Nordigen, params)

            case Operation.BankDel:
                with self.db.session() as session:
                    session.remove_by_name(Bank, params)

            case Operation.PSD2Del:
                with self.db.session() as session:
                    session.remove_by_name(Nordigen, params)

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
                | Operation.PSD2Add
                | Operation.RuleAdd
                | Operation.TagAdd
                | Operation.TagRuleAdd
            ):
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
                if not (
                    isinstance(params[0], int)
                    and all(isinstance(p, int) for p in params[1])
                ):
                    raise TypeError("f{params} are not transaction ids")

                with self.db.session() as session:
                    original = session.get(Transaction, Transaction.id, params[0])[0]
                    links = session.get(Transaction, Transaction.id, params[1])

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
                    session.add(tobelinked)

            case Operation.Dismantle:
                assert all(isinstance(param, Link) for param in params)

                with self.db.session() as session:
                    original = params[0].original
                    links = [link.link for link in params]
                    session.remove_links(original, links)

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

                with self.db.session() as session:
                    originals = session.get(Transaction, Transaction.id, [original.id])
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

                    session.add(transactions)

            case Operation.Export:
                with self.db.session() as session:
                    self.dump(params[0], params[1], sorted(session.get(Transaction)))

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
                            category["name"],
                            CategorySelector(category["selector"]["selector"]),
                        )

                    transactions.append(transaction)

                if self.certify(transactions):
                    with self.db.session() as session:
                        session.add(transactions)

            case Operation.ExportBanks:
                with self.db.session() as session:
                    self.dump(params[0], params[1], session.get(Bank))

            case Operation.ImportBanks:
                banks = []
                for row in self.load(params[0], params[1]):
                    bank = Bank(row["name"], row["BIC"], row["type"])
                    if row["nordigen"]:
                        bank.nordigen = Nordigen(**row["nordigen"])
                    banks.append(bank)

                if self.certify(banks):
                    with self.db.session() as session:
                        session.add(banks)

            case Operation.ExportCategoryRules:
                with self.db.session() as session:
                    self.dump(params[0], params[1], session.get(CategoryRule))

            case Operation.ImportCategoryRules:
                rules = [CategoryRule(**row) for row in self.load(params[0], params[1])]

                if self.certify(rules):
                    with self.db.session() as session:
                        session.add(rules)

            case Operation.ExportTagRules:
                with self.db.session() as session:
                    self.dump(params[0], params[1], session.get(TagRule))

            case Operation.ImportTagRules:
                rules = [TagRule(**row) for row in self.load(params[0], params[1])]

                if self.certify(rules):
                    with self.db.session() as session:
                        session.add(rules)

            case Operation.ExportCategories:
                with self.db.session() as session:
                    self.dump(params[0], params[1], session.get(Category))

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

                        category.rules = set(CategoryRule(**rule) for rule in rules)
                    if row["schedule"]:
                        category.schedule = CategorySchedule(**row["schedule"])
                    categories.append(category)

                if self.certify(categories):
                    with self.db.session() as session:
                        session.add(categories)

            case Operation.ExportCategoryGroups:
                with self.db.session() as session:
                    self.dump(params[0], params[1], session.get(CategoryGroup))

            case Operation.ImportCategoryGroups:
                groups = [
                    CategoryGroup(**row) for row in self.load(params[0], params[1])
                ]

                if self.certify(groups):
                    with self.db.session() as session:
                        session.add(groups)

    def parse(self, filename: Path, args: dict):
        return parse_data(filename, args)

    def askcategory(self, transaction: Transaction):
        selector = CategorySelector(Selector_T.manual)

        with self.db.session() as session:
            categories = session.get(Category)

            while True:
                category = input(f"{transaction}: ")
                if category in [c.name for c in categories]:
                    return TransactionCategory(category, selector)

    @staticmethod
    def dump(fn, format, sequence):
        if format == "pickle":
            with open(fn, "wb") as f:
                pickle.dump([e.format for e in sequence], f)
        elif format == "csv":
            with open(fn, "w", newline="") as f:
                csv.writer(f).writerows([e.format.values() for e in sequence])
        else:
            print("format not well specified")

    @staticmethod
    def load(fn, format):
        if format == "pickle":
            with open(fn, "rb") as f:
                return pickle.load(f)
        elif format == "csv":
            raise Exception("CSV import not supported")
        else:
            print("format not well specified")
            return []

    @staticmethod
    def certify(imports: list) -> bool:
        if input(f"{imports[:10]}\nDoes the import seem correct? (y/n)") == "y":
            return True
        return False

    @property
    def db(self) -> DbClient:
        return DbClient(self._db, self._verbosity > 2)

    @db.setter
    def db(self, url: str):
        self._db = url

    @staticmethod
    def nordigen_client() -> NordigenClient:
        return NordigenClient(NordigenCredentialsManager.default)
