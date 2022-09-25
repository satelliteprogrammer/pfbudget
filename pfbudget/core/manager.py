from pfbudget.core.input.parsers import parse_data
from pfbudget.core.transactions import Transaction
from pfbudget.db.client import DatabaseClient
from pfbudget.utils.converters import convert


class Manager:
    def __init__(self, db: str):
        self.__db = DatabaseClient(db)

    def transactions() -> list[Transaction]:
        pass

    def add_transactions(self, transactions: list[Transaction]):
        converted = convert(transactions)
        self.__db.insert_transactions(converted)

    def parse(self, filename: str, args: dict):
        transactions = parse_data(filename, args)
        self.add_transactions(transactions)
