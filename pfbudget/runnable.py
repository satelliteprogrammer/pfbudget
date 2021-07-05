from pathlib import Path
import argparse

from .categories import categorize_data
from .database import DBManager
from .parsers import parse_data
import pfbudget.graph
import pfbudget.report
import pfbudget.utils

DEFAULT_DB = "data.db"


class PfBudgetInitialized(Exception):
    pass


class PfBudgetNotInitialized(Exception):
    pass


class DataFileMissing(Exception):
    pass


def argparser() -> argparse.ArgumentParser:
    help = argparse.ArgumentParser(add_help=False)
    help.add_argument(
        "-db", "--database", help="select current database", default=DEFAULT_DB
    )
    help.add_argument("-q", "--quiet", help="quiet")

    parser = argparse.ArgumentParser(
        description="does cool finance stuff", parents=[help]
    )
    parser.add_argument("--version")

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="sub-command help"
    )

    """
    Init
    """
    p_init = subparsers.add_parser("init", parents=[help])
    p_init.set_defaults(func=lambda args: DBManager(args.database).init())

    """
    Exporting
    """
    p_export = subparsers.add_parser("export", parents=[help])
    p_export.set_defaults(func=lambda args: DBManager(args.database).export())

    """
    Parsing
    """
    p_parse = subparsers.add_parser("parse", parents=[help])
    p_parse.add_argument("path", nargs="+", type=str)
    p_parse.add_argument("--bank", nargs=1, type=str)
    p_parse.set_defaults(func=parse)

    """
    Categorizing
    """
    p_categorize = subparsers.add_parser("categorize", parents=[help])
    p_categorize.set_defaults(
        func=lambda args: categorize_data(DBManager(args.database))
    )

    period = argparse.ArgumentParser(add_help=False).add_mutually_exclusive_group()
    period.add_argument(
        "--interval", type=str, nargs=2, help="graph interval", metavar=("START", "END")
    )
    period.add_argument("--start", type=str, nargs=1, help="graph start date")
    period.add_argument("--end", type=str, nargs=1, help="graph end date")
    period.add_argument("--year", type=str, nargs=1, help="graph year")

    """
    Graph
    """
    p_graph = subparsers.add_parser("graph", parents=[help, period])
    p_graph.add_argument(
        "option",
        type=str,
        choices=["monthly", "discrete"],
        nargs="?",
        default="monthly",
        help="graph option help",
    )
    p_graph.set_defaults(func=graph)

    """
    Report
    """
    p_report = subparsers.add_parser("report", parents=[help, period])
    p_report.set_defaults(func=report)

    p_status = subparsers.add_parser("status", help="status help")

    p_status.set_defaults(func=status)

    return parser


def parse(args):
    """Parses the contents of the path in args to the selected database.

    Args:
        args (dict): argparse variables
    """
    db = DBManager(args.database)
    for path in args.path:
        if (dir := Path(path)).is_dir():
            for file in dir.iterdir():
                parse_data(db, file, args.bank)
        elif Path(path).is_file():
            parse_data(db, path, args.bank)
        else:
            raise FileNotFoundError


def status(state, args):
    """Status

    Prints the state file.

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    """
    print(state)


def graph(args):
    """Plots the transactions over a period of time.

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    """
    start, end = pfbudget.utils.parse_args_period(args)
    if args.option == "monthly":
        pfbudget.graph.monthly(DBManager(args.database), start, end)
    elif args.option == "discrete":
        pfbudget.graph.discrete(DBManager(args.database), start, end)


def report(args):
    """Prints a detailed report of the transactions over a period of time.

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    """
    start, end = pfbudget.utils.parse_args_period(args)
    pfbudget.report.net(DBManager(args.database), start, end)


def run():
    args = argparser().parse_args()
    args.func(args)
