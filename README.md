# Personal Finance Budget (`pfbudget`)

A budgeting tool for those who want full control and transparency over their finances.

## Features

- **Bank Data Ingestion:**
  - Download transactions directly from banks via a PSD2 aggregator (using the GoCardless API).
  - Or, parse CSV bank extracts using configurable YAML-based parsers (parsers.yaml).
- **Database Storage:**
  - All transactions and categorization rules are stored in a PostgreSQL database.
- **Rules-Based Categorization:**
  - Automatically categorize transactions using rules stored in the database.
  - Interactive mode for manual categorization of remaining transactions.

> **Note:** Graphical reporting is currently broken. For now, you can run SQL queries directly on the database for custom reports.

## Quick Start

### 1. Install dependencies

This project uses [Poetry](https://python-poetry.org/):

```sh
poetry install
```

### 2. Configure

- **Database:**
  Set up a PostgreSQL database and configure your connection through a `.env` file.
- **GoCardless credentials:**
  Create an account with GoCardless (previously Nordigen) and save them on the `.env` file.
- **Bank Parsers:**
  For CSV parsing, edit `parsers.yaml` to match your bank’s CSV format.
  If the CSV is more complex than the basic rules can handle, you can enable `additional_parser: true` and implement a parser class in `pfbudget/extract/parsers.py`. The `Bank1` is an example implementation.

### 3. Run

You can run the app as a module:

```sh
poetry run python3 -m pfbudget [options]
```

#### Example workflows

- **Download from bank aggregator:**
  First step is to accept an End User Agreement with the bank in question to get access to your own data:
  ```sh
  poetry run python3 -m pfbudget eua your_bank
  ```
  ```sh
  poetry run python3 -m pfbudget download --banks your_bank
  ```
- **Parse CSV:**
  ```sh
  poetry run python3 -m pfbudget parse --bank your_bank export.csv
  ```

- **Automatic categorization:**
  ```sh
  poetry run python3 -m pfbudget categorize auto
  ```

- **Interactive categorization:**
  ```sh
  poetry run python3 -m pfbudget categorize manual
  ```

## Available Commands

The CLI supports a variety of operations. Here are the main commands:

- **export**: Export transactions to a specified file and format.
- **import**: Import transactions from a specified file and format.
- **parse**: Parse transactions from CSV files (with optional bank and credit card arguments).
- **categorize**
  - `auto`: Automatically categorize transactions using rules.
  - `manual`: Manually categorize uncategorized transactions.
- **bank**
  - `add`, `del`, `mod`: Manage bank definitions.
  - `psd2`: Manage PSD2 bank connections.
  - `export`, `import`: Export/import bank definitions.
- **token**: Manage PSD2 access tokens.
- **eua**: Manage PSD2 requisition IDs.
- **download**: Download transactions from banks via PSD2 API.
- **banks**: List available banks in a country.
- **category**
  - `add`, `remove`, `update`, `schedule`: Manage categories.
  - `rule`: Manage categorization rules (add, remove, modify, export, import).
  - `group`: Manage category groups (add, remove, export, import).
  - `export`, `import`: Export/import categories.
- **tag**
  - `add`, `remove`: Manage tags.
  - `rule`: Manage tag rules (add, remove, modify, export, import).
- **link**
  - `forge`, `dismantle`: Link or unlink transactions.

Each command may have additional options and subcommands. For details, run:

```sh
poetry run python3 -m pfbudget --help
```

or for a specific command:

```sh
poetry run python3 -m pfbudget <command> --help
```

---

**License:** GPL-3.0-or-later
**Author:** Luís Murta <luis@murta.dev>
