from dataclasses import dataclass
from decimal import Decimal

CREATE_TRANSACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS "transactions" (
    "date" TEXT NOT NULL,
    "description" TEXT,
    "bank" TEXT NOT NULL,
    "value" REAL NOT NULL,
    "category" TEXT,
    "original" TEXT,
    "additional comments" TEXT
);
"""


@dataclass
class DbTransaction:
    date: str
    description: str
    bank: str
    value: Decimal
    category: str
    original: str
    comments: str

    def tuple(self) -> tuple:
        return (
            self.date,
            self.description,
            self.bank,
            self.value,
            self.category,
        )


DbTransactions = list[DbTransaction]

CREATE_BACKUPS_TABLE = """
CREATE TABLE IF NOT EXISTS backups (
    datetime TEXT NOT NULL,
    file TEXT NOT NULL
)
"""

CREATE_BANKS_TABLE = """
CREATE TABLE IF NOT EXISTS banks (
    name TEXT NOT NULL PRIMARY KEY,
    bic TEXT,
    nordigen_id TEXT,
    nordigen_name TEXT,
    requisition_id TEXT,
    invert INTEGER,
    offset INTEGER
)
"""


@dataclass
class DbBank:
    name: str
    bic: str
    nordigen_id: str
    nordigen_name: str
    requisition_id: str
    invert: bool = False
    offset: int = 0

    def tuple(self):
        return (
            self.name,
            self.bic,
            self.nordigen_id,
            self.nordigen_name,
            self.requisition_id,
            int(self.invert),
            self.offset,
        )


DbBanks = list[DbBank]

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
ORDER BY date ASC
"""

SORTED_TRANSACTIONS = """
SELECT *
FROM transactions
ORDER BY date ASC
"""

SELECT_TRANSACTIONS_BETWEEN_DATES = """
SELECT *
FROM transactions
WHERE date BETWEEN (?) AND (?)
ORDER BY date ASC
"""

SELECT_TRANSACTIONS_BY_CATEGORY = """
SELECT *
FROM transactions
WHERE category IS (?)
ORDER BY date ASC
"""

SELECT_TRANSACTIONS_BETWEEN_DATES_WITH_CATEGORY = """
SELECT *
FROM transactions
WHERE date BETWEEN (?) AND (?)
AND category IS (?)
ORDER BY date ASC
"""

SELECT_TRANSACTION_BY_PERIOD = """
SELECT EXTRACT((?) FROM date) AS (?), date, description, bank, value
FROM transactions
ORDER BY date ASC
"""

SELECT_TRANSACTIONS_BETWEEN_DATES_WITHOUT_CATEGORIES = """
SELECT *
FROM transactions
WHERE date BETWEEN (?) AND (?)
AND category NOT IN {}
ORDER BY date ASC
"""

ADD_BANK = """
INSERT INTO banks (name, bic, nordigen_id, nordigen_name, requisition_id, invert) values (?,?,?,?,?,?)
"""

DELETE_BANK = """
DELETE FROM banks
WHERE name = (?)
"""

SELECT_BANK = """
SELECT *
FROM banks
WHERE {} = (?)
"""

SELECT_BANKS = """
SELECT *
FROM banks
"""
