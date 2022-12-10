from pfbudget.input.input import Input
from pfbudget.input.nordigen import NordigenClient
from pfbudget.input.parsers import parse_data
from pfbudget.db.client import DbClient
from pfbudget.db.model import Category, CategoryGroup, CategoryRule, CategorySchedule
from pfbudget.common.types import Operation
from pfbudget.core.categorizer import Categorizer
from pfbudget.utils import convert

from pfbudget.cli.runnable import download, parse


class Manager:
    def __init__(self, db: str, args: dict):
        self._args = args
        print(args)

        self._db = db

    def action(self, op: Operation, params: list):
        match (op):
            case Operation.Init:
                pass
            case Operation.Parse:
                # TODO this is a monstrosity, remove when possible
                parse(self, self.args)
            case Operation.Download:
                # TODO this is a monstrosity, remove when possible
                download(self, self.args)
            case Operation.Categorize:
                with self.db.session() as session:
                    uncategorized = session.uncategorized()
                    categories = session.categories()
                    Categorizer().categorize(uncategorized, categories)

            case Operation.Register:
                # self._db = DbClient(args["database"])
                # self.register(args)
                pass
            case Operation.Unregister:
                # self._db = DbClient(args["database"])
                # self.unregister(args)
                pass
            case Operation.Token:
                NordigenClient(self).token()

            case Operation.Renew:
                NordigenClient(self).requisition(
                    self.args["name"], self.args["country"]
                )

            case Operation.CategoryAdd:
                with self.db.session() as session:
                    session.addcategories(params)

            case Operation.CategoryUpdate:
                with self.db.session() as session:
                    session.updategroup(*params)

            case Operation.CategoryRemove:
                with self.db.session() as session:
                    session.removecategories(params)

            case Operation.CategorySchedule:
                with self.db.session() as session:
                    session.updateschedules(params)

            case Operation.CategoryRule:
                with self.db.session() as session:
                    session.addrules(params)

            case Operation.GroupAdd:
                with self.db.session() as session:
                    for group in self.args["group"]:
                        session.addcategorygroup(CategoryGroup(name=group))

            case Operation.GroupRemove:
                with self.db.session() as session:
                    session.removecategorygroup(
                        [CategoryGroup(name=group) for group in self.args["group"]]
                    )

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

    def parser(self, parser: Input):
        transactions = parser.parse()
        print(transactions)
        # self.add_transactions(transactions)

    # def parse(self, filename: str):
    #     transactions = parse_data(filename, self.args)
    #     self.add_transactions(transactions)

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
        return DbClient(self._db, self.args["verbose"])

    @db.setter
    def db(self, url: str):
        self._db = url

    @property
    def args(self) -> dict:
        return self._args
