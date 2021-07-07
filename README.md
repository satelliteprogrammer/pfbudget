# Personal Finance Budget (pfbudget)

parse -> categorize -> analyze (predict) -> present

## Parse
Parses bank extracts, based on parsers.yaml, to a SQLite database.

## Categorize
Categorizes transactions based on categories.yaml configuration.

### Reserved categories and groups
There is 1 special category and 2 reserved groups.

The `Null` category represent transactions performed between banks/credit cards, that would otherwise appear in the reports and graph. This way, these transactions, while real, are shadowed from the information presented. The net effect of these transaction, if performed in the same month would be moot anyway, since they cancel each other, but could introduce visual pollution when separated for a few days, especial when spawning through different months. The `Null` category then present a placeholder category for these transactions, as well as a way to preserve them out of side.
ToDo: As a side bonus, whenever these don't cancel eachother, a warning could be shown.

The 2 reserved groups are `income` and `investment`.
The `income` is used for all income categories. These are the ones that will have a net effect on the overall balance of the individual, and are normally expected to be shown against expenses.
The `investment` group is separated from the remaining expenses, has these might not only present in absolute terms much higher values than other categories, but will also be subject to a different treatment when market predictions are incorporated.

## Analyze (ToDo)
Analyzes previous transaction and predicts future expenses.

## Present
Create graphs and reports
1. Monthly spending from everyday purchases
2. Networth with big expenses tagged in (ToDo)
3. Future trajectory with predictable costs included (ToDo)

## ToDo
- [ ] Support regular transactions from fixed group in categories
- [ ] Predicting future expenses
- [ ] Finish writing the README.md
- [ ] Implement undo/redo feature in sqlite3 database
- [ ] Allow for the possibility to create a new parser during runtime by guessing from transaction list/user input
- [ ] Allow for transaction to be passed as argument to main.py
