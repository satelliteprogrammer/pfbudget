import sqlite3

import logging
import logging.config


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
                return cur.fetchall()
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
