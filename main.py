from pathlib import Path
import argparse
import datetime as dt

from pfbudget.graph import monthly
from pfbudget.transactions import load_transactions, save_transactions
import pfbudget.tools as tools


p = ".pfbudget/state"


class PfBudgetInitialized(Exception):
    pass


class PfBudgetNotInitialized(Exception):
    pass


class DataFileMissing(Exception):
    pass


def init(state, args):
    """init function

    Creates state file which stores the internal state of the program for later use.
    Calls parse, that parses all raw directory into data directory.

    args.raw -- raw dir
    args.data -- data dir
    """
    if not state:
        s = dict(
            filename=p,
            raw_dir=args.raw,
            data_dir=args.data,
            raw_files=[],
            data_files=[],
            vacations=[],
            last_backup="",
            last_datadir_backup="",
        )
        state = tools.pfstate(p, s)
        parse(state, args)
    else:
        raise PfBudgetInitialized()


def restart(state, args):
    """restart function

    Deletes state and creates new one. Parses all raw directory into data directory.
    New dirs can be passed as arguments, otherwise uses previous values.

    args.raw -- raw dir
    args.data -- data dir
    """
    if state is not None:
        for fn in state.data_files:
            try:
                (Path(state.data_dir) / fn).unlink()
            except FileNotFoundError:
                raise DataFileMissing("missing {}".format(Path(state.data_dir) / fn))

        if args.raw:
            state.raw_dir = args.raw
        if args.data:
            state.data_dir = args.data
        state.raw_files = []
        state.data_files = []
        parse(state, args)
    else:
        raise PfBudgetNotInitialized()


def backup(state, args):
    """backup function

    Saves all transactions on transactions_#.csv
    """
    if args.option == "single":
        tools.backup(state)
    elif args.option == "all":
        tools.full_backup(state)
    elif args.option == "restore":
        tools.restore(state)


def parse(state, args):
    """parse function

    Extracts from .pfbudget.pickle the already read files and parses the remaining.
    args will be None if called from command line and gathered from the pickle.

    args.raw -- raw dir
    args.data -- data dir
    """
    raw_dir = args.raw if hasattr(args, "raw") else None
    data_dir = args.data if hasattr(args, "data") else None

    tools.parser(state, raw_dir, data_dir)
    categorize(state, args)


def categorize(state, args):
    """categorize function

    Automatically categorizes transactions based on the regex of each Category
    """
    transactions = load_transactions(state.data_dir)
    missing = tools.auto_categorization(state, transactions)
    if missing:
        tools.manual_categorization(state, transactions)
    save_transactions(state.data_dir, transactions)


def vacation(state, args):
    """vacation function

    Adds vacations to the pfstate
    date(2019, 12, 23), date(2020, 1, 2)
    date(2020, 7, 1), date(2020, 7, 30)
    """
    print(args)
    if args.option == "list":
        print(state.vacations)
    elif args.option == "remove":
        vacations = state.vacations
        del state.vacations[args.pos[0]]
        state.vacations = vacations
    elif args.option == "add":
        start = dt.datetime.strptime(args.start[0], "%Y/%m/%d").date()
        end = dt.datetime.strptime(args.end[0], "%Y/%m/%d").date()

        vacations = state.vacations
        vacations.append((start, end))
        state.vacations = vacations


def status(state, args):
    print(state)


def graph(state, args):
    monthly(state, start=dt.date(2020, 1, 1), end=dt.date(2020, 12, 31))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="does cool finance stuff")
    parser.add_argument("-q", "--quiet", help="quiet")

    subparsers = parser.add_subparsers(
        dest="task", required=True, help="sub-command help"
    )

    p_init = subparsers.add_parser("init", help="init help")
    p_restart = subparsers.add_parser("restart", help="restart help")
    p_backup = subparsers.add_parser("backup", help="backup help")
    p_parse = subparsers.add_parser("parse", help="parse help")
    p_vacation = subparsers.add_parser(
        "vacation", help="vacation help format: [YYYY/MM/DD]"
    )
    p_graph = subparsers.add_parser("graph", help="graph help")
    p_report = subparsers.add_parser("report", help="report help")
    p_status = subparsers.add_parser("status", help="status help")

    p_init.add_argument("raw", help="the raw data dir")
    p_init.add_argument("data", help="the parsed data dir")
    p_init.set_defaults(func=init)

    p_restart.add_argument("--raw", help="new raw data dir")
    p_restart.add_argument("--data", help="new parsed data dir")
    p_restart.set_defaults(func=restart)

    p_backup.add_argument(
        "option",
        type=str,
        choices=["single", "all", "restore"],
        nargs="?",
        default="single",
        help="backup option help",
    )

    subparser_vacation = p_vacation.add_subparsers(
        dest="option", required=True, help="vacation suboption help"
    )
    p_vacation_add = subparser_vacation.add_parser("add", help="add help")
    p_vacation_add.add_argument(
        "start", type=str, nargs=1, help="new vacation start date"
    )
    p_vacation_add.add_argument("end", type=str, nargs=1, help="new vacation end date")
    p_vacation_list = subparser_vacation.add_parser("list", help="list help")
    p_vacation_remove = subparser_vacation.add_parser("remove", help="remove help")
    p_vacation_remove.add_argument(
        "pos", help="position of vacation to remove", type=int, nargs=1
    )

    p_backup.set_defaults(func=backup)
    p_parse.set_defaults(func=parse)
    p_vacation.set_defaults(func=vacation)
    p_status.set_defaults(func=status)
    p_graph.set_defaults(func=graph)

    state = tools.pfstate(p)
    state.filename = p
    args = parser.parse_args()
    args.func(state, args)

    # income = [sum(t.value for cat, transactions in months.items() for t in transactions
    #                     if cat in get_income_categories()) for months in monthly_transactions_by_cat]

    # expenses = []
    # for category in expense_categories:
    #     expense_value = [-sum(t.value for t in month[category]) for month in monthly_transactions_by_cat]
    #     expenses.extend(expense_value)

    # print("Income: {}, Expenses: {}, Net = {}"".format(sum(income), sum(expenses), sum(income) - sum(expenses)))
