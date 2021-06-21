from __future__ import annotations
import csv
import datetime
import logging
import logging.config
import pathlib
import sqlite3
from decimal import Decimal

from .transactions import Transaction


if not pathlib.Path("logs").is_dir():
    pathlib.Path("logs").mkdir()
logging.config.fileConfig("logging.conf")
logger = logging.getLogger("pfbudget.transactions")

sqlite3.register_adapter(Decimal, lambda d: float(d))

__DB_NAME = "data.db"

CREATE_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS transactions (
    date TEXT NOT NULL,
    description TEXT,
    bank TEXT,
    value REAL NOT NULL,
    category TEXT
);
"""

CREATE_BACKUPS_TABLE = """
CREATE TABLE IF NOT EXISTS backups (
    datetime TEXT NOT NULL,
    file TEXT NOT NULL
)
"""

CREATE_BANKS_TABLE = """
CREATE TABLE banks (
    name TEXT NOT NULL PRIMARY KEY,
    url TEXT
)
"""

ADD_TRANSACTION = """
INSERT INTO transactions (date, description, bank, value, category) values (?,?,?,?,?)
"""

UPDATE_CATEGORY = """
UPDATE transactions
SET category = (?)
WHERE date = (?) AND description = (?) AND bank = (?) AND value = (?)
"""

DUPLICATED_TRANSACTIONS = """
SELECT COUNT(*), date, description, bank, value
FROM transactions
GROUP BY date, description, bank, value
HAVING COUNT(*) > 1
"""

SORTED_TRANSACTIONS = """
SELECT *
FROM transactions
ORDER BY (?)
"""

SELECT_TRANSACTIONS_BETWEEN_DATES = """
SELECT *
FROM transactions
WHERE date BETWEEN (?) AND (?)
"""

SELECT_TRANSACTIONS_BY_CATEGORY = """
SELECT *
FROM transactions
WHERE category IS (?)
"""

SELECT_TRANSACTION_BY_PERIOD = """
SELECT EXTRACT((?) FROM date) AS (?), date, description, bank, value
FROM transactions
"""

SELECT_TRANSACTIONS_BETWEEN_DATES_WITHOUT_CATEGORIES = """
SELECT *
FROM transactions
WHERE date BETWEEN (?) AND (?)
AND category NOT IN {}
"""


class DBManager:
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
            logger.info(f"Creating table if it doesn't exist {table_name}")
            self.__execute(query)

    def init(self):
        self.__create_tables(
            (
                ("transactions", CREATE_TRANSACTIONS_TABLE),
                ("backups", CREATE_BACKUPS_TABLE),
            )
        )

    def select_all(self):
        logger.info(f"Reading all transactions from {self.db}")
        return self.__execute("SELECT * FROM transactions")

    def insert_transaction(self, transaction: Transaction):
        logger.info(f"Adding {transaction} into {self.db}")
        self.__execute(ADD_TRANSACTION, (transaction.to_list(),))

    def insert_transactions(self, transactions: list[Transaction]):
        logger.info(f"Adding {len(transactions)} into {self.db}")
        transactions = [t.to_list() for t in transactions]
        self.__executemany(ADD_TRANSACTION, transactions)

    def update_category(self, transaction: Transaction):
        logger.info(f"Update {transaction} category")
        self.__execute(UPDATE_CATEGORY, (transaction[4], *transaction[:4]))

    def update_categories(self, transactions: list[Transaction]):
        logger.info(f"Update {len(transactions)} transactions' categories")
        self.__executemany(
            UPDATE_CATEGORY, [transaction for transaction in transactions]
        )

    def get_duplicated_transactions(self) -> list[Transaction] | None:
        logger.info("Get duplicated transactions")
        transactions = self.__execute(DUPLICATED_TRANSACTIONS)
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def get_sorted_transactions(self, key: str) -> list[Transaction] | None:
        logger.info(f"Get transactions sorted by {key}")
        transactions = self.__execute(SORTED_TRANSACTIONS, key)
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def get_daterange(self, start: datetime, end: datetime) -> list[Transaction] | None:
        logger.info(f"Get transactions from {start} to {end}")
        transactions = self.__execute(SELECT_TRANSACTIONS_BETWEEN_DATES, (start, end))
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def get_category(self, value: str) -> list[Transaction] | None:
        logger.info(f"Get transaction where category = {value}")
        transactions = self.__execute(SELECT_TRANSACTIONS_BY_CATEGORY, (value,))
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def get_by_period(self, period: str) -> list[Transaction] | None:
        logger.info(f"Get transactions by {period}")
        transactions = self.__execute(SELECT_TRANSACTION_BY_PERIOD, period)
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def get_uncategorized_transactions(self) -> list[Transaction] | None:
        logger.info("Get uncategorized transactions")
        transactions = self.get_category(None)
        if transactions:
            return [Transaction(t) for t in transactions]
        return None

    def get_daterage_without(
        self, start: datetime, end: datetime, *categories: str
    ) -> list[Transaction] | None:
        logger.info(f"Get transactions between {start} and {end} not in {categories}")
        query = SELECT_TRANSACTIONS_BETWEEN_DATES_WITHOUT_CATEGORIES.format(
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
        logger.info(f"Exporting {self.db} into {filename}")
        transactions = self.select_all()
        if not (dir := pathlib.Path(self.__EXPORT_DIR)).is_dir():
            dir.mkdir()
        with open(dir / filename, "w", newline="") as f:
            csv.writer(f, delimiter="\t").writerows(transactions)
