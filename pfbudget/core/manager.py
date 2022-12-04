from pfbudget.input.input import Input
from pfbudget.input.nordigen import NordigenClient
from pfbudget.input.parsers import parse_data
from pfbudget.db.client import DbClient
from pfbudget.common.types import Command
from pfbudget.core.categorizer import Categorizer
from pfbudget.utils import convert

from pfbudget.cli.runnable import download, parse


class Manager:
    def __init__(self, command: Command):
        self.__command = command
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

    def start(self, args):
        match (self.__command):
            case Command.Init:
                pass
            case Command.Parse:
                # TODO this is a monstrosity, remove when possible
                self._db = DbClient(args["database"])
                parse(self, args)
            case Command.Download:
                # TODO this is a monstrosity, remove when possible
                self._db = DbClient(args["database"])
                download(self, args)
            case Command.Categorize:
                self._db = DbClient(args["database"])
                self.categorize(args)
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
                NordigenClient(self).requisition(args["name"], args["country"])

    # def init(self):
    #     client = DatabaseClient(self.__db)
    #     client.init()

    # def register(self, args: dict):
    #     bank = Bank(args["bank"][0], "", args["requisition"][0], args["invert"])
    #     client = DatabaseClient(self.__db)
    #     client.register_bank(convert(bank))

    # def unregister(self, args: dict):
    #     client = DatabaseClient(self.__db)
    #     client.unregister_bank(args["bank"][0])

    def parser(self, parser: Input):
        transactions = parser.parse()
        print(transactions)
        # self.add_transactions(transactions)

    # def parse(self, filename: str, args: dict):
    #     transactions = parse_data(filename, args)
    #     self.add_transactions(transactions)

    # def transactions() -> list[Transaction]:
    #     pass

    def add_transactions(self, transactions):
        with self.db.session() as session:
            session.add(transactions)
            session.commit()

    def categorize(self, args: dict):
        with self.db.session() as session:
            uncategorized = session.uncategorized()
            Categorizer().categorize(uncategorized)
            session.commit()

    # def get_bank_by(self, key: str, value: str) -> Bank:
    #     client = DatabaseClient(self.__db)
    #     bank = client.get_bank(key, value)
    #     return convert(bank)

    def get_banks(self):
        return self.db.get_nordigen_banks()

    @property
    def db(self):
        return self._db
