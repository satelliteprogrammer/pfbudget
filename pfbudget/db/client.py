from __future__ import annotations
from decimal import Decimal
import csv
import datetime
import logging
import logging.config
import pathlib
import sqlite3

from pfbudget.common.types import Transaction
import pfbudget.db.schema as Q


if not pathlib.Path("logs").is_dir():
    pathlib.Path("logs").mkdir()
logging.config.fileConfig("logging.conf")
logger = logging.getLogger("pfbudget.transactions")

sqlite3.register_adapter(Decimal, lambda d: float(d))

__DB_NAME = "data.db"


class DatabaseClient:
    """SQLite DB connection manager"""

    __EXPORT_DIR = "export"

    def __init__(self, db: str):
        self.db = db

    def __execute(self, query: str, params: tuple = None) -> list | None:
        ret = None
        try:
            con = sqlite3.connect(self.db)
            with con:
                if params:
                    ret = con.execute(query, params).fetchall()
                    logger.debug(f"[{self.db}] < {query}{params}")
                else:
                    ret = con.execute(query).fetchall()
                    logger.debug(f"[{self.db}] < {query}")

                if ret:
                    logger.debug(f"[{self.db}] > {ret}")
        except sqlite3.Error:
            logger.exception(f"Error while executing [{self.db}] < {query}")
        finally:
            con.close()

        return ret

    def __executemany(self, query: str, list_of_params: list[tuple]) -> list | None:
        ret = None
        try:
            con = sqlite3.connect(self.db)
            with con:
                ret = con.executemany(query, list_of_params).fetchall()
                logger.debug(f"[{self.db}] < {query}{list_of_params}")
        except sqlite3.Error:
            logger.exception(
                f"Error while executing [{self.db}] < {query} {list_of_params}"
            )
        finally:
            con.close()

        return ret

    def __create_tables(self, tables: tuple[tuple]):
        for table_name, query in tables:
            logger.info(f"Creating table {table_name} if it doesn't exist already")
            self.__execute(query)

    def init(self):
        logging.info(f"Initializing {self.db} database")
        self.__create_tables(
            (
                ("transactions", Q.CREATE_TRANSACTIONS_TABLE),
                ("backups", Q.CREATE_BACKUPS_TABLE),
                ("banks", Q.CREATE_BANKS_TABLE),
            )
        )

    """Transaction table methods"""

    def select_all(self) -> list[Transaction] | None:
        logger.info(f"Reading all transactions from {self.db}")
        transactions = self.__execute("SELECT * FROM transactions")
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def insert_transaction(self, transaction: Transaction):
        logger.info(f"Adding {transaction} into {self.db}")
        self.__execute(Q.ADD_TRANSACTION, (transaction.to_list(),))

    def insert_transactions(self, transactions: Q.DbTransactions):
        logger.info(f"Adding {len(transactions)} into {self.db}")
        self.__executemany(Q.ADD_TRANSACTION, [t.tuple() for t in transactions])

    def update_category(self, transaction: Transaction):
        logger.info(f"Update {transaction} category")
        self.__execute(Q.UPDATE_CATEGORY, transaction.update_category())

    def update_categories(self, transactions: list[Transaction]):
        logger.info(f"Update {len(transactions)} transactions' categories")
        self.__executemany(
            Q.UPDATE_CATEGORY,
            [transaction.update_category() for transaction in transactions],
        )

    def get_duplicated_transactions(self) -> list[Transaction] | None:
        logger.info("Get duplicated transactions")
        transactions = self.__execute(Q.DUPLICATED_TRANSACTIONS)
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def get_sorted_transactions(self) -> list[Transaction] | None:
        logger.info("Get transactions sorted by date")
        transactions = self.__execute(Q.SORTED_TRANSACTIONS)
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def get_daterange(self, start: datetime, end: datetime) -> list[Transaction] | None:
        logger.info(f"Get transactions from {start} to {end}")
        transactions = self.__execute(Q.SELECT_TRANSACTIONS_BETWEEN_DATES, (start, end))
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def get_category(self, value: str) -> list[Transaction] | None:
        logger.info(f"Get transactions where category = {value}")
        transactions = self.__execute(Q.SELECT_TRANSACTIONS_BY_CATEGORY, (value,))
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def get_daterange_category(
        self, start: datetime, end: datetime, category: str
    ) -> list[Transaction] | None:
        logger.info(
            f"Get transactions from {start} to {end} where category = {category}"
        )
        transactions = self.__execute(
            Q.SELECT_TRANSACTIONS_BETWEEN_DATES_WITH_CATEGORY, (start, end, category)
        )
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def get_by_period(self, period: str) -> list[Transaction] | None:
        logger.info(f"Get transactions by {period}")
        transactions = self.__execute(Q.SELECT_TRANSACTION_BY_PERIOD, period)
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def get_uncategorized_transactions(self) -> list[Transaction] | None:
        logger.debug("Get uncategorized transactions")
        return self.get_category(None)

    def get_daterange_uncategorized_transactions(self, start: datetime, end: datetime):
        logger.debug("Get uncategorized transactions from {start} to {end}")
        return self.get_daterange_category(start, end, None)

    def get_daterage_without(
        self, start: datetime, end: datetime, *categories: str
    ) -> list[Transaction] | None:
        logger.info(f"Get transactions between {start} and {end} not in {categories}")
        query = Q.SELECT_TRANSACTIONS_BETWEEN_DATES_WITHOUT_CATEGORIES.format(
            "(" + ", ".join("?" for _ in categories) + ")"
        )
        transactions = self.__execute(query, (start, end, *categories))
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def export(self):
        filename = pathlib.Path(
            "@".join([self.db, datetime.datetime.now().isoformat()])
        ).with_suffix(".csv")
        transactions = self.select_all()
        logger.info(f"Exporting {self.db} into {filename}")
        if not (dir := pathlib.Path(self.__EXPORT_DIR)).is_dir():
            dir.mkdir()
        with open(dir / filename, "w", newline="") as f:
            csv.writer(f, delimiter="\t").writerows(transactions)

    """Banks table methods"""

    def register_bank(self, bank: Q.DbBank):
        logger.info(f"Registering {bank}")
        self.__execute(Q.ADD_BANK, bank.tuple())

    def unregister_bank(self, bank: str):
        logger.info(f"Unregistering {bank}")
        self.__execute(Q.DELETE_BANK, (bank,))

    def get_bank(self, key: str, value: str) -> Q.DbBank | None:
        logger.info(f"Get bank with {key} = {value}")
        bank = self.__execute(Q.SELECT_BANK.format(key), (value, ))
        if bank:
            return Q.DbBank(*bank[0])

    def get_banks(self) -> Q.DbBanks:
        logger.info("Get all banks")
        banks = self.__execute(Q.SELECT_BANKS)
        if banks:
            return [Q.DbBank(*bank) for bank in banks]
        return []
