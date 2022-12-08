from pfbudget.input.input import Input
from pfbudget.input.nordigen import NordigenClient
from pfbudget.input.parsers import parse_data
from pfbudget.db.client import DbClient
from pfbudget.db.model import Category, CategoryGroup
from pfbudget.common.types import Command, Operation
from pfbudget.core.categorizer import Categorizer
from pfbudget.utils import convert

from pfbudget.cli.runnable import download, parse


class Manager:
    def __init__(self, command: Command, args: dict):
        self.__command = command
        self._args = args
        match (command):
            case Command.Init:
                pass
            case Command.Parse:
                pass
            case Command.Download:
                pass
            case Command.Categorize:
                pass
            case Command.Register:
                pass
            case Command.Unregister:
                pass
            case Command.Token:
                pass
            case Command.Renew:
                pass
            case Command.Category:
                pass

        assert "database" in args, "ArgParser didn't include db"
        self._db = args["database"]

    def start(self):
        match (self.__command):
            case Command.Init:
                pass
            case Command.Parse:
                # TODO this is a monstrosity, remove when possible
                parse(self, self.args)
            case Command.Download:
                # TODO this is a monstrosity, remove when possible
                download(self, self.args)
            case Command.Categorize:
                self.categorize(self.args)
            case Command.Register:
                # self._db = DbClient(args["database"])
                # self.register(args)
                pass
            case Command.Unregister:
                # self._db = DbClient(args["database"])
                # self.unregister(args)
                pass
            case Command.Token:
                NordigenClient(self).token()

            case Command.Renew:
                NordigenClient(self).requisition(
                    self.args["name"], self.args["country"]
                )

            case Command.Category:
                assert "op" in self.args, "category operation not defined"

                with self.db.session() as session:
                    match self.args["op"]:
                        case Operation.Add:
                            for category in self.args["category"]:
                                session.addcategory(
                                    Category(name=category, group=self.args["group"])
                                )

                        case Operation.Remove:
                            session.removecategory(
                                [
                                    Category(name=category)
                                    for category in self.args["category"]
                                ]
                            )

                        case Operation.UpdateGroup:
                            session.updategroup(
                                [
                                    Category(name=category)
                                    for category in self.args["category"]
                                ],
                                self.args["group"][0],
                            )

                        case Operation.AddGroup:
                            for group in self.args["group"]:
                                session.addcategorygroup(CategoryGroup(name=group))

                        case Operation.RemoveGroup:
                            session.removecategorygroup(
                                [
                                    CategoryGroup(name=group)
                                    for group in self.args["group"]
                                ]
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
