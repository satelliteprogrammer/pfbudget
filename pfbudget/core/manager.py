from pfbudget.core.input.input import Input
from pfbudget.core.input.parsers import parse_data
from pfbudget.core.transactions import Transaction
from pfbudget.db.client import DatabaseClient
from pfbudget.db.schema import Bank
from pfbudget.utils.converters import convert


class Manager:
    def __init__(self, db: str):
        self.db = db

    def init(self):
        client = DatabaseClient(self.db)
        client.init()

    def register(self, args: dict):
        print(args)
        client = DatabaseClient(self.db)
        client.register_bank(
            Bank(
                (
                    args["bank"][0],
                    args["requisition"][0]
                    if args["requisition"]
                    else args["requisition"],
                    args["invert"],
                    args["description"],
                )
            )
        )

    def unregister(self, args: dict):
        client = DatabaseClient(self.db)
        client.unregister_bank(args["bank"][0])

    def parser(self, parser: Input):
        print(parser.parse())

    def parse(self, filename: str, args: dict):
        transactions = parse_data(filename, args)
        self.add_transactions(transactions)

    def transactions() -> list[Transaction]:
        pass

    def add_transactions(self, transactions: list[Transaction]):
        converted = convert(transactions)
        self.__db.insert_transactions(converted)
