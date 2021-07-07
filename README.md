# Personal Finance Budget (pfbudget)

parse -> categorize -> analyze (predict) -> present

## Parse
Parses bank extracts, based on parsers.yaml, to a SQLite database.

## Categorize
Categorizes transactions based on categories.yaml configuration.

## Analyze (ToDo)
Analyzes previous transaction and predicts future expenses.

## Present
Create graphs and reports
1. Monthly spending from everyday purchases
2. Networth with big expenses tagged in (ToDo)
3. Future trajectory with predictable costs included (ToDo)

## ToDo
- [ ] Predicting future expenses
- [ ] Finish writing the README.md
- [ ] Implement undo/redo feature in sqlite3 database
- [ ] Allow for the possibility to create a new parser during runtime by guessing from transaction list/user input
- [ ] Allow for transaction to be passed as argument to main.py
