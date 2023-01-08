from pathlib import Path

from pfbudget.common.types import Operation
from pfbudget.core.categorizer import Categorizer
from pfbudget.db.client import DbClient
from pfbudget.db.model import (
    Bank,
    Category,
    CategoryGroup,
    CategoryRule,
    CategorySchedule,
    Nordigen,
    Rule,
    Tag,
    TagRule,
)
from pfbudget.input.nordigen import NordigenInput
from pfbudget.input.parsers import parse_data
from pfbudget.output.csv import CSV
from pfbudget.output.output import Output


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
                for path in params[0]:
                    if (dir := Path(path)).is_dir():
                        for file in dir.iterdir():
                            transactions.extend(self.parse(file, args))
                    elif Path(path).is_file():
                        transactions.extend(self.parse(path, args))
                    else:
                        raise FileNotFoundError(path)

                print(transactions)
                if len(transactions) > 0 and input("Commit? (y/n)") == "y":
                    self.add_transactions(sorted(transactions))

            case Operation.Download:
                client = NordigenInput()
                client.banks = self.get_banks()
                client.start = params[0]
                client.end = params[1]
                transactions = client.parse()
                self.add_transactions(transactions)

            case Operation.Categorize:
                with self.db.session() as session:
                    uncategorized = session.uncategorized()
                    categories = session.categories()
                    tags = session.tags()
                    Categorizer().categorize(uncategorized, categories, tags)

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
                NordigenInput().requisition(params[0], params[1])

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
                    session.add(CategoryGroup(params))

            case Operation.GroupRemove:
                assert all(isinstance(param, CategoryGroup) for param in params)
                with self.db.session() as session:
                    session.remove_by_name(CategoryGroup, params)

            case Operation.Forge:
                with self.db.session() as session:
                    session.add(params)

            case Operation.Dismantle:
                with self.db.session() as session:
                    original = params[0].original
                    links = [link.link for link in params]
                    session.remove_links(original, links)

            case Operation.Export:
                with self.db.session() as session:
                    if len(params) < 4:
                        banks = [bank.name for bank in session.banks()]
                        transactions = session.transactions(params[0], params[1], banks)
                    else:
                        transactions = session.transactions(
                            params[0], params[1], params[2]
                        )

                    csvwriter: Output = CSV(params[-1])
                    csvwriter.report(transactions)

    # def init(self):
    #     client = DatabaseClient(self.__db)
    #     client.init()

    # def register(self):
    #     bank = Bank(self.args["bank"][0], "", self.args["requisition"][0], self.args["invert"])
    #     client = DatabaseClient(self.__db)
    #     client.register_bank(convert(bank))

    # def unregister(self):
    #     client = DatabaseClient(self.__db)
    #     client.unregister_bank(self.args["bank"][0])

    def parse(self, filename: str, args: dict):
        return parse_data(filename, args)

    # def transactions() -> list[Transaction]:
    #     pass

    def add_transactions(self, transactions):
        with self.db.session() as session:
            session.add(transactions)

    # def get_bank_by(self, key: str, value: str) -> Bank:
    #     client = DatabaseClient(self.__db)
    #     bank = client.get_bank(key, value)
    #     return convert(bank)

    def get_banks(self):
        return self.db.get_nordigen_banks()

    @property
    def db(self) -> DbClient:
        return DbClient(self._db, self._verbosity > 2)

    @db.setter
    def db(self, url: str):
        self._db = url
