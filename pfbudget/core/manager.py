from pfbudget.input.input import Input
from pfbudget.input.parsers import parse_data
from pfbudget.common.types import Bank, Banks, Transaction, Transactions
from pfbudget.db.client import DatabaseClient
from pfbudget.utils import convert


class Manager:
    def __init__(self, db: str):
        self.__db = db

    def init(self):
        client = DatabaseClient(self.__db)
        client.init()

    def register(self, args: dict):
        print(args)
        client = DatabaseClient(self.__db)
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
        client = DatabaseClient(self.__db)
        client.unregister_bank(args["bank"][0])

    def parser(self, parser: Input):
        transactions = parser.parse()
        self.add_transactions(transactions)

    def parse(self, filename: str, args: dict):
        transactions = parse_data(filename, args)
        self.add_transactions(transactions)

    def transactions() -> list[Transaction]:
        pass

    def add_transactions(self, transactions: Transactions):
        client = DatabaseClient(self.__db)
        client.insert_transactions([convert(t) for t in transactions])

    def get_bank_by(self, key: str, value: str) -> Bank:
        client = DatabaseClient(self.__db)
        bank = client.get_bank(key, value)
        return convert(bank)

    def get_banks(self) -> Banks:
        client = DatabaseClient(self.__db)
        return [convert(bank) for bank in client.get_banks()]
