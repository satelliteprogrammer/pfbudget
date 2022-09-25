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
