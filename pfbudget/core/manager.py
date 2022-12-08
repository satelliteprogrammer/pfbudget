from pfbudget.input.input import Input
from pfbudget.input.nordigen import NordigenClient
from pfbudget.input.parsers import parse_data
from pfbudget.db.client import DbClient
from pfbudget.db.model import Category, CategoryGroup, CategorySchedule
from pfbudget.common.types import Operation
from pfbudget.core.categorizer import Categorizer
from pfbudget.utils import convert

from pfbudget.cli.runnable import download, parse


class Manager:
    def __init__(self, op: Operation, args: dict):
        self._operation = op
        self._args = args

        assert "database" in args, "ArgParser didn't include db"
        self._db = args["database"]

    def start(self):
        match (self._operation):
            case Operation.Init:
                pass
            case Operation.Parse:
                # TODO this is a monstrosity, remove when possible
                parse(self, self.args)
            case Operation.Download:
                # TODO this is a monstrosity, remove when possible
                download(self, self.args)
            case Operation.Categorize:
                self.categorize()

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
                    for category in self.args["category"]:
                        session.addcategory(
                            Category(name=category, group=self.args["group"])
                        )

            case Operation.CategoryUpdate:
                with self.db.session() as session:
                    session.updategroup(
                        [Category(name=category) for category in self.args["category"]],
                        self.args["group"][0],
                    )

            case Operation.CategoryRemove:
                with self.db.session() as session:
                    session.removecategory(
                        [Category(name=category) for category in self.args["category"]]
                    )

            case Operation.CategorySchedule:
                assert (
                    "period" in self.args and "frequency" in self.args
                ), "Schedule not well defined"

                with self.db.session() as session:
                    session.updateschedules(
                        [Category(name=category) for category in self.args["category"]],
                        CategorySchedule(
                            recurring=True,
                            period=self.args["period"][0],
                            period_multiplier=self.args["frequency"][0],
                        ),
                    )

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

    def categorize(self):
        with self.db.session() as session:
            uncategorized = session.uncategorized()
            Categorizer().categorize(uncategorized)

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
