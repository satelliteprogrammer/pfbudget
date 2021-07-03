from pathlib import Path
import argparse
import datetime as dt

from .categories import categorize_data
from .database import DBManager
from .graph import discrete, monthly
from .parsers import parse_data
from . import report

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

    """
    Graph
    """
    p_graph = subparsers.add_parser("graph", parents=[help])
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
    p_graph.set_defaults(func=graph)

    p_report = subparsers.add_parser("report", help="report help")
    p_status = subparsers.add_parser("status", help="status help")

    p_status.set_defaults(func=status)
    p_report.set_defaults(func=f_report)

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
    start, end = dt.date.min, dt.date.max
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
        monthly(DBManager(args.database), start, end)
    elif args.option == "discrete":
        discrete(DBManager(args.database), start, end)


def f_report(state, args):
    """Report

    Prints a detailed report of the transactions over a period of time.

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    """
    report.net(state)


def run():
    args = argparser().parse_args()
    args.func(args)
