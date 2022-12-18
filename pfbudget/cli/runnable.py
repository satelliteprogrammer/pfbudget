from pathlib import Path
import argparse
import datetime as dt
import decimal
import re

from pfbudget.common.types import Operation
from pfbudget.core.categories import categorize_data
from pfbudget.db.model import Period
from pfbudget.input.json import JsonParser
from pfbudget.input.nordigen import NordigenInput
from pfbudget.db.sqlite import DatabaseClient
import pfbudget.reporting.graph
import pfbudget.reporting.report
import pfbudget.utils


DEFAULT_DB = "data.db"


class PfBudgetInitialized(Exception):
    pass


class PfBudgetNotInitialized(Exception):
    pass


class DataFileMissing(Exception):
    pass


def argparser() -> argparse.ArgumentParser:

    universal = argparse.ArgumentParser(add_help=False)
    universal.add_argument(
        "-db",
        "--database",
        nargs="?",
        help="select current database",
        default=DEFAULT_DB,
    )
    universal.add_argument(
        "-q", "--quiet", action="store_true", help="reduces the amount of verbose"
    )
    universal.add_argument(
        "-v", "--verbose", action="store_true", help="increases the amount of verbose"
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
        parents=[universal],
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

    subparsers = parser.add_subparsers(required=True)

    """
    Init
    """
    p_init = subparsers.add_parser(
        "init",
        description="Initializes the SQLite3 database",
        parents=[universal],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_init.set_defaults(command=Operation.Init)

    """
    Exporting
    """
    p_export = subparsers.add_parser(
        "export",
        description="Exports the selected database to a .csv file",
        parents=[universal],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_export.set_defaults(func=lambda args: DatabaseClient(args.database).export())

    """
    Parsing
    """
    p_parse = subparsers.add_parser(
        "parse",
        description="Parses and adds the requested transactions into the selected database",
        parents=[universal],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_parse.add_argument("path", nargs="+", type=str)
    p_parse.add_argument("--bank", nargs=1, type=str)
    p_parse.add_argument("--creditcard", nargs=1, type=str)
    p_parse.add_argument("--category", nargs=1, type=int)
    p_parse.set_defaults(command=Operation.Parse)

    """
    Categorizing
    """
    categorize = subparsers.add_parser(
        "categorize",
        description="Categorizes the transactions in the selected database",
        parents=[universal],
    )
    categorize.set_defaults(op=Operation.Categorize)

    """
    Graph
    """
    p_graph = subparsers.add_parser(
        "graph",
        description="Graph of the transactions",
        parents=[universal, period],
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
        parents=[universal, period],
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
    Register bank
    """
    p_register = subparsers.add_parser(
        "register",
        description="Register a bank",
        parents=[universal],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_register.add_argument("bank", type=str, nargs=1, help="bank option help")
    p_register.add_argument(
        "--requisition", type=str, nargs=1, help="requisition option help"
    )
    p_register.add_argument("--invert", action="store_true")
    p_register.set_defaults(command=Operation.Register)

    """
    Unregister bank
    """
    p_register = subparsers.add_parser(
        "unregister",
        description="Unregister a bank",
        parents=[universal],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_register.add_argument("bank", type=str, nargs=1, help="bank option help")
    p_register.set_defaults(command=Operation.Unregister)

    """
    Nordigen API
    """
    p_nordigen_access = subparsers.add_parser(
        "token",
        description="Get new access token",
        parents=[universal],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_nordigen_access.set_defaults(command=Operation.Token)

    """
    (Re)new bank requisition ID
    """
    p_nordigen_access = subparsers.add_parser(
        "renew",
        description="(Re)new the Bank requisition ID",
        parents=[universal],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_nordigen_access.add_argument("name", nargs=1, type=str)
    p_nordigen_access.add_argument("country", nargs=1, type=str)
    p_nordigen_access.set_defaults(command=Operation.Renew)

    """
    Downloading through Nordigen API
    """
    p_nordigen_download = subparsers.add_parser(
        "download",
        description="Downloads transactions using Nordigen API",
        parents=[universal, period],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_nordigen_download.add_argument("--id", nargs="+", type=str)
    p_nordigen_download.add_argument("--name", nargs="+", type=str)
    p_nordigen_download.add_argument("--all", action="store_true")
    p_nordigen_download.set_defaults(command=Operation.Download)

    # """
    # List available banks on Nordigen API
    # """
    # p_nordigen_list = subparsers.add_parser(
    #     "list",
    #     description="Lists banks in {country}",
    #     parents=[help],
    #     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    # )
    # p_nordigen_list.add_argument("country", nargs=1, type=str)
    # p_nordigen_list.set_defaults(func=lambda args: nordigen_banks(manager, args))

    # """
    # Nordigen JSONs
    # """
    # p_nordigen_json = subparsers.add_parser(
    #     "json",
    #     description="",
    #     parents=[help],
    #     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    # )
    # p_nordigen_json.add_argument("json", nargs=1, type=str)
    # p_nordigen_json.add_argument("bank", nargs=1, type=str)
    # p_nordigen_json.add_argument("--invert", action=argparse.BooleanOptionalAction)
    # p_nordigen_json.set_defaults(
    #     func=lambda args: manager.parser(JsonParser(vars(args)))
    # )

    # Categories
    category_parser = subparsers.add_parser("category", parents=[universal])
    category(category_parser, universal)

    # Tag
    tags(subparsers.add_parser("tag", parents=[universal]), universal)

    return parser


def parse(manager, args):
    """Parses the contents of the path in args to the selected database.

    Args:
        args (dict): argparse variables
    """
    for path in args.path:
        if (dir := Path(path)).is_dir():
            for file in dir.iterdir():
                manager.parse(file, vars(args))
        elif Path(path).is_file():
            manager.parse(path, vars(args))
        else:
            raise FileNotFoundError


def graph(args):
    """Plots the transactions over a period of time.

    Args:
        args (dict): argparse variables
    """
    start, end = pfbudget.utils.parse_args_period(args)
    if args.option == "monthly":
        pfbudget.reporting.graph.monthly(
            DatabaseClient(args.database), vars(args), start, end
        )
    elif args.option == "discrete":
        pfbudget.reporting.graph.discrete(
            DatabaseClient(args.database), vars(args), start, end
        )
    elif args.option == "networth":
        pfbudget.reporting.graph.networth(
            DatabaseClient(args.database), vars(args), start, end
        )


def report(args):
    """Prints a detailed report of the transactions over a period of time.

    Args:
        args (dict): argparse variables
    """
    start, end = pfbudget.utils.parse_args_period(args)
    if args.option == "net":
        pfbudget.reporting.report.net(DatabaseClient(args.database), start, end)
    elif args.option == "detailed":
        pfbudget.reporting.report.detailed(DatabaseClient(args.database), start, end)


# def nordigen_banks(manager: Manager, args):
#     input = NordigenInput(manager)
#     input.list(vars(args)["country"][0])


def download(manager, args: dict):
    start, end = pfbudget.utils.parse_args_period(args)
    manager.parser(NordigenInput(manager, args, start, end))


def category(parser: argparse.ArgumentParser, universal: argparse.ArgumentParser):
    commands = parser.add_subparsers(required=True)

    add = commands.add_parser("add", parents=[universal])
    add.set_defaults(op=Operation.CategoryAdd)
    add.add_argument("category", nargs="+", type=str)
    add.add_argument("--group", nargs="?", type=str)

    remove = commands.add_parser("remove", parents=[universal])
    remove.set_defaults(op=Operation.CategoryRemove)
    remove.add_argument("category", nargs="+", type=str)

    update = commands.add_parser("update", parents=[universal])
    update.set_defaults(op=Operation.CategoryUpdate)
    update.add_argument("category", nargs="+", type=str)
    update.add_argument("--group", nargs="?", type=str)

    schedule = commands.add_parser("schedule", parents=[universal])
    schedule.set_defaults(op=Operation.CategorySchedule)
    schedule.add_argument("category", nargs="+", type=str)
    schedule.add_argument("period", nargs=1, choices=[e.value for e in Period])
    schedule.add_argument("--frequency", nargs=1, default=[1], type=int)

    rule = commands.add_parser("rule", parents=[universal])
    category_rule(rule, universal)

    group = commands.add_parser("group", parents=[universal])
    category_group(group, universal)


def category_group(parser: argparse.ArgumentParser, universal: argparse.ArgumentParser):
    commands = parser.add_subparsers(required=True)

    add = commands.add_parser("add", parents=[universal])
    add.set_defaults(op=Operation.GroupAdd)
    add.add_argument("group", nargs="+", type=str)

    remove = commands.add_parser("remove", parents=[universal])
    remove.set_defaults(op=Operation.GroupRemove)
    remove.add_argument("group", nargs="+", type=str)


def category_rule(parser: argparse.ArgumentParser, universal: argparse.ArgumentParser):
    commands = parser.add_subparsers(required=True)

    add = commands.add_parser("add", parents=[universal])
    add.set_defaults(op=Operation.RuleAdd)
    add.add_argument("category", nargs="+", type=str)
    rules(add)

    remove = commands.add_parser("remove", parents=[universal])
    remove.set_defaults(op=Operation.RuleRemove)
    remove.add_argument("id", nargs="+", type=int)

    modify = commands.add_parser("modify", parents=[universal])
    modify.set_defaults(op=Operation.RuleModify)
    modify.add_argument("id", nargs="+", type=int)
    modify.add_argument("--category", nargs=1, type=str)
    rules(modify)


def tags(parser: argparse.ArgumentParser, universal: argparse.ArgumentParser):

    commands = parser.add_subparsers(required=True)

    add = commands.add_parser("add", parents=[universal])
    add.set_defaults(op=Operation.TagAdd)
    add.add_argument("tag", nargs="+", type=str)

    remove = commands.add_parser("remove", parents=[universal])
    remove.set_defaults(op=Operation.TagRemove)
    remove.add_argument("tag", nargs="+", type=str)

    rule = commands.add_parser("rule", parents=[universal])
    tag_rule(rule, universal)


def tag_rule(parser: argparse.ArgumentParser, universal: argparse.ArgumentParser):
    commands = parser.add_subparsers(required=True)

    add = commands.add_parser("add", parents=[universal])
    add.set_defaults(op=Operation.TagRuleAdd)
    add.add_argument("tag", nargs="+", type=str)
    rules(add)

    remove = commands.add_parser("remove", parents=[universal])
    remove.set_defaults(op=Operation.TagRuleRemove)
    remove.add_argument("id", nargs="+", type=int)

    modify = commands.add_parser("modify", parents=[universal])
    modify.set_defaults(op=Operation.TagRuleModify)
    modify.add_argument("id", nargs="+", type=int)
    modify.add_argument("--tag", nargs=1, type=str)
    rules(modify)


def rules(parser: argparse.ArgumentParser):
    parser.add_argument("--date", nargs=1, type=dt.date.fromisoformat)
    parser.add_argument("--description", nargs=1, type=str)
    parser.add_argument("--regex", nargs=1, type=str)
    parser.add_argument("--bank", nargs=1, type=str)
    parser.add_argument("--min", nargs=1, type=decimal.Decimal)
    parser.add_argument("--max", nargs=1, type=decimal.Decimal)


def run():
    args = vars(argparser().parse_args())
    assert "op" in args, "No operation selected"
    return args["op"], args
