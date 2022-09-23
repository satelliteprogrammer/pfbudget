from pathlib import Path
import argparse
import re

from pfbudget.core.categories import categorize_data
from pfbudget.core.input.parsers import parse_data
from pfbudget.db.client import DBManager
import pfbudget.reporting.graph
import pfbudget.reporting.report
import pfbudget.utils

from pfbudget.core.input.nordigen import Client


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
        "-db",
        "--database",
        nargs="?",
        help="select current database",
        default=DEFAULT_DB,
    )
    help.add_argument(
        "-q", "--quiet", action="store_true", help="reduces the amount of verbose"
    )

    period = argparse.ArgumentParser(add_help=False).add_mutually_exclusive_group()
    period.add_argument(
        "--interval", type=str, nargs=2, help="graph interval", metavar=("START", "END")
    )
    period.add_argument("--start", type=str, nargs=1, help="graph start date")
    period.add_argument("--end", type=str, nargs=1, help="graph end date")
    period.add_argument("--year", type=str, nargs=1, help="graph year")

    parser = argparse.ArgumentParser(
        description="does cool finance stuff",
        parents=[help],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=re.search(
            r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
            open("pfbudget/__init__.py").read(),
        ).group(1),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    """
    Init
    """
    p_init = subparsers.add_parser(
        "init",
        description="Initializes the SQLite3 database",
        parents=[help],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_init.set_defaults(func=lambda args: DBManager(args.database).init())

    """
    Exporting
    """
    p_export = subparsers.add_parser(
        "export",
        description="Exports the selected database to a .csv file",
        parents=[help],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_export.set_defaults(func=lambda args: DBManager(args.database).export())

    """
    Parsing
    """
    p_parse = subparsers.add_parser(
        "parse",
        description="Parses and adds the requested transactions into the selected database",
        parents=[help],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_parse.add_argument("path", nargs="+", type=str)
    p_parse.add_argument("--bank", nargs=1, type=str)
    p_parse.add_argument("--creditcard", nargs=1, type=str)
    p_parse.add_argument("--category", nargs=1, type=int)
    p_parse.set_defaults(func=parse)

    """
    Categorizing
    """
    p_categorize = subparsers.add_parser(
        "categorize",
        description="Categorizes the transactions in the selected database",
        parents=[help],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_categorize.set_defaults(
        func=lambda args: categorize_data(DBManager(args.database))
    )

    """
    Graph
    """
    p_graph = subparsers.add_parser(
        "graph",
        description="Graph of the transactions",
        parents=[help, period],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_graph.add_argument(
        "option",
        type=str,
        choices=["monthly", "discrete", "networth"],
        nargs="?",
        default="monthly",
        help="graph option help",
    )
    p_graph.add_argument("--save", action="store_true")
    p_graph.set_defaults(func=graph)

    """
    Report
    """
    p_report = subparsers.add_parser(
        "report",
        description="Prints report of transaction groups",
        parents=[help, period],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_report.add_argument(
        "option",
        type=str,
        choices=["net", "detailed"],
        nargs="?",
        default="net",
        help="report option help",
    )
    p_report.set_defaults(func=report)

    """
    Init Nordigen session: get new access token
    """
    p_nordigen_access = subparsers.add_parser(
        "init",
        description="Get new access token",
        parents=[help],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_nordigen_access.set_defaults(func=lambda args: Client().token())

    """
    Access to Nordigen API
    """
    p_nordigen_access = subparsers.add_parser(
        "renew",
        description="Renew the requisition ID",
        parents=[help],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_nordigen_access.add_argument("institution", nargs=1, type=str)
    p_nordigen_access.add_argument("country", nargs=1, type=str)
    p_nordigen_access.set_defaults(
        func=lambda args: Client().requisition(args.institution[0], args.country[0])
    )

    """
    Downloading through Nordigen API
    """
    p_nordigen_download = subparsers.add_parser(
        "download",
        description="Downloads transactions using Nordigen API",
        parents=[help],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_nordigen_download.add_argument("id", nargs=1, type=str)
    p_nordigen_download.set_defaults(func=lambda args: Client().download(args.id[0]))

    """
    List available banks to download from
    """
    p_nordigen_list = subparsers.add_parser(
        "list",
        description="Lists banks in {country}",
        parents=[help],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_nordigen_list.add_argument("country", nargs=1, type=str)
    p_nordigen_list.set_defaults(func=lambda args: Client().banks(args.country[0]))

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
                parse_data(db, file, vars(args))
        elif Path(path).is_file():
            parse_data(db, path, vars(args))
        else:
            raise FileNotFoundError


def graph(args):
    """Plots the transactions over a period of time.

    Args:
        args (dict): argparse variables
    """
    start, end = pfbudget.utils.parse_args_period(args)
    if args.option == "monthly":
        pfbudget.reporting.graph.monthly(DBManager(args.database), vars(args), start, end)
    elif args.option == "discrete":
        pfbudget.reporting.graph.discrete(DBManager(args.database), vars(args), start, end)
    elif args.option == "networth":
        pfbudget.reporting.graph.networth(DBManager(args.database), vars(args), start, end)


def report(args):
    """Prints a detailed report of the transactions over a period of time.

    Args:
        args (dict): argparse variables
    """
    start, end = pfbudget.utils.parse_args_period(args)
    if args.option == "net":
        pfbudget.reporting.report.net(DBManager(args.database), start, end)
    elif args.option == "detailed":
        pfbudget.reporting.report.detailed(DBManager(args.database), start, end)


def run():
    args = argparser().parse_args()
    args.func(args)
