import sqlite3

import logging
import logging.config
import pathlib


if not pathlib.Path("logs").is_dir():
    pathlib.Path("logs").mkdir()
logging.config.fileConfig("logging.conf")
logger = logging.getLogger("pfbudget.transactions")

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
WHERE category = (?)
"""

SELECT_TRANSACTION_BY_PERIOD = """
SELECT EXTRACT((?) FROM date) AS (?), date, description, bank, value
FROM transactions
"""


class Connection:
    """SQLite DB connection manager"""

    def __init__(self, db_name):
        self.db_name = db_name
        self.connection = None

        self.__open()
        self.__create_tables((("transactions", CREATE_TRANSACTIONS_TABLE),))

    def __open(self):
        try:
            self.connection = sqlite3.connect(self.db_name)
            logger.debug(f"SQLite database {self.db_name} connection successful")
        except sqlite3.Error:
            logger.exception(f"Error while connection to {self.db_name}")

    def close(self):
        try:
            self.connection.close()
            logger.debug(f"SQLite database {self.db_name} closed")
        except sqlite3.Error:
            logger.exception(f"Error while closing {self.db_name} database")

    def __execute(self, query, params=None):
        try:
            with self.connection:
                if params:
                    cur = self.connection.execute(query, params)
                    logger.debug(f"[{self.db_name}] < {query}{params}")
                else:
                    cur = self.connection.execute(query)
                    logger.debug(f"[{self.db_name}] < {query}")

                if ret := cur.fetchall():
                    logger.debug(f"[{self.db_name}] > {ret}")
                return ret
        except sqlite3.Error:
            logger.exception(f"Error while executing [{self.db_name}] < {query}")

    def __executemany(self, query, list_of_params):
        try:
            with self.connection:
                cur = self.connection.executemany(query, list_of_params)
                logger.debug(f"[{self.db_name}] < {query}{list_of_params}")
                return cur.fetchall()
        except sqlite3.Error:
            logger.exception(
                f"Error while executing [{self.db_name}] < {query} {list_of_params}"
            )

    def __create_tables(self, tables):
        for table_name, query in tables:
            logger.info(f"Creating table if it doesn't exist {table_name}")
            self.__execute(query)

    def select_all(self):
        logger.info(f"Reading all transactions from {self.db_name}")
        return self.__execute("SELECT * FROM transactions")

    def add_transaction(self, transaction):
        logger.info(f"Adding {transaction} into {self.db_name}")
        self.__execute(ADD_TRANSACTION, transaction)

    def add_transactions(self, transactions):
        logger.info(f"Adding {len(transactions)} into {self.db_name}")
        self.__executemany(ADD_TRANSACTION, transactions)

    def update_category(self, transaction):
        logger.info(f"Update {transaction} category")
        self.__execute(UPDATE_CATEGORY, (transaction[4], *transaction[:4]))

    def get_duplicated_transactions(self):
        logger.info("Get duplicated transactions")
        return self.__execute(DUPLICATED_TRANSACTIONS)

    def get_sorted_transactions(self, key):
        logger.info(f"Get transactions sorted by {key}")
        return self.__execute(SORTED_TRANSACTIONS, key)

    def get_daterange(self, start, end):
        logger.info(f"Get transactions from {start} to {end}")
        return self.__execute(SELECT_TRANSACTIONS_BETWEEN_DATES, (start, end))

    def get_category(self, value):
        logger.info(f"Get transaction where category = {value}")
        return self.__execute(SELECT_TRANSACTIONS_BY_CATEGORY, (value,))

    def get_by_period(self, period):
        logger.info(f"Get transactions by {period}")
        return self.__execute(SELECT_TRANSACTION_BY_PERIOD, period)

    def query(self, query, params=None):
        logger.info(f"Executing {query} with params={params}")
        return self.__execute(query, params)
