from pathlib import Path
import argparse
import datetime as dt

from .categories import categorize_data
from .database import DBManager
from .graph import discrete, monthly
from .parsers import parse_data
from .transactions import load_transactions, save_transactions
from . import report

DEFAULT_DB = "data.db"


class PfBudgetInitialized(Exception):
    pass


class PfBudgetNotInitialized(Exception):
    pass


class DataFileMissing(Exception):
    pass


def argparser():
    parser = argparse.ArgumentParser(description="does cool finance stuff")
    parser.add_argument("--db", help="select current database", default=DEFAULT_DB)
    parser.add_argument("-q", "--quiet", help="quiet")
    parser.add_argument("--version")

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="sub-command help"
    )

    """
    Init
    """
    p_init = subparsers.add_parser("init", help="init help")
    p_init.set_defaults(func=lambda args: DBManager(args.db))

    """
    Exporting
    """
    p_export = subparsers.add_parser("export", help="export help")
    p_export.set_defaults(func=lambda args: DBManager(args.db).export())

    """
    Parsing
    """
    p_parse = subparsers.add_parser("parse", help="parse help")
    p_parse.add_argument("path", nargs="+", type=str)
    p_parse.add_argument("--bank", nargs=1, type=str)
    p_parse.set_defaults(func=parse)

    """
    Categorizing
    """
    p_categorize = subparsers.add_parser("categorize", help="parse help")
    p_categorize.set_defaults(func=categorize)

    p_vacation = subparsers.add_parser(
        "vacation", help="vacation help format: [YYYY/MM/DD]"
    )
    p_graph = subparsers.add_parser("graph", help="graph help")
    p_report = subparsers.add_parser("report", help="report help")
    p_status = subparsers.add_parser("status", help="status help")

    subparser_vacation = p_vacation.add_subparsers(
        dest="option", required=True, help="vacation suboption help"
    )
    p_vacation_add = subparser_vacation.add_parser("add", help="add help")
    p_vacation_add.add_argument(
        "start", type=str, nargs=1, help="new vacation start date"
    )
    p_vacation_add.add_argument("end", type=str, nargs=1, help="new vacation end date")
    _ = subparser_vacation.add_parser("list", help="list help")
    p_vacation_remove = subparser_vacation.add_parser("remove", help="remove help")
    p_vacation_remove.add_argument(
        "pos", help="position of vacation to remove", type=int, nargs=1
    )

    p_graph.add_argument(
        "option",
        type=str,
        choices=["monthly", "discrete"],
        nargs="?",
        default="monthly",
        help="graph option help",
    )
    p_graph_interval = p_graph.add_mutually_exclusive_group()
    p_graph_interval.add_argument(
        "--interval", type=str, nargs=2, help="graph interval", metavar=("START", "END")
    )
    p_graph_interval.add_argument("--start", type=str, nargs=1, help="graph start date")
    p_graph_interval.add_argument("--end", type=str, nargs=1, help="graph end date")
    p_graph_interval.add_argument("--year", type=str, nargs=1, help="graph year")

    # p_restart.set_defaults(func=restart)
    p_vacation.set_defaults(func=vacation)
    p_status.set_defaults(func=status)
    p_graph.set_defaults(func=graph)
    p_report.set_defaults(func=f_report)

    return parser


def parse(args, db):
    """Parser

    Parses the contents of the raw directory into the data files, and
    categorizes the transactions

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    """
    for path in args.path:
        if (dir := Path(path)).is_dir():
            for file in dir.iterdir():
                parse_data(file, args.bank)
        elif Path(path).is_file():
            trs = parse_data(path, args.bank)
        else:
            raise FileNotFoundError
    print("\n".join([t.desc() for t in trs]))


def categorize(args, db):
    """Categorization

    Automatically categorizes transactions based on the regex of each
    category. Manually present the remaining to the user

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    """
    categorize_data(db)


def vacation(state, args):
    """Vacations

    Adds vacations to the pfstate.

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    """
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
    """Status

    Prints the state file.

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    """
    print(state)


def graph(state, args):
    """Graph

    Plots the transactions over a period of time.

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    """
    start, end = None, None
    if args.start or args.interval:
        start = dt.datetime.strptime(args.start[0], "%Y/%m/%d").date()

    if args.end or args.interval:
        end = dt.datetime.strptime(args.end[0], "%Y/%m/%d").date()

    if args.interval:
        start = dt.datetime.strptime(args.interval[0], "%Y/%m/%d").date()
        end = dt.datetime.strptime(args.interval[1], "%Y/%m/%d").date()

    if args.year:
        start = dt.datetime.strptime(args.year[0], "%Y").date()
        end = dt.datetime.strptime(
            str(int(args.year[0]) + 1), "%Y"
        ).date() - dt.timedelta(days=1)

    if args.option == "monthly":
        monthly(state, start, end)
    elif args.option == "discrete":
        discrete(state, start, end)


def f_report(state, args):
    """Report

    Prints a detailed report of the transactions over a period of time.

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    """
    report.net(state)


def run():
    db = DBManager("transactions.db")
    args = argparser().parse_args()
    args.func(args, db)
