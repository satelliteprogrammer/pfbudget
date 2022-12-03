from pfbudget.input.input import Input
from pfbudget.input.parsers import parse_data
from pfbudget.db.client import DbClient
from pfbudget.utils import convert


class Manager:
    def __init__(self, url: str):
        self._db = DbClient(url)

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

    # def get_bank_by(self, key: str, value: str) -> Bank:
    #     client = DatabaseClient(self.__db)
    #     bank = client.get_bank(key, value)
    #     return convert(bank)

    def get_banks(self):
        return self.db.get_nordigen_banks()

    @property
    def db(self):
        return self._db
