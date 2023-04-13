import argparse
import datetime as dt
import decimal
from dotenv import load_dotenv
import os
import re

from pfbudget.common.types import Operation
from pfbudget.db.model import AccountType, Period

from pfbudget.db.sqlite import DatabaseClient
import pfbudget.reporting.graph
import pfbudget.reporting.report
import pfbudget.utils.utils

load_dotenv()

DEFAULT_DB = os.environ.get("DEFAULT_DB")


def argparser() -> argparse.ArgumentParser:
    universal = argparse.ArgumentParser(add_help=False)
    universal.add_argument(
        "-db",
        "--database",
        nargs="?",
        help="select current database",
        default=DEFAULT_DB,
    )

    universal.add_argument("-v", "--verbose", action="count", default=0)

    period = argparse.ArgumentParser(add_help=False)
    period_group = period.add_mutually_exclusive_group()
    period_group.add_argument(
        "--interval", type=str, nargs=2, help="graph interval", metavar=("START", "END")
    )
    period_group.add_argument("--start", type=str, nargs=1, help="graph start date")
    period_group.add_argument("--end", type=str, nargs=1, help="graph end date")
    period_group.add_argument("--year", type=str, nargs=1, help="graph year")

    parser = argparse.ArgumentParser(
        description="does cool finance stuff",
        parents=[universal],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    if version := re.search(
        r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]', open("pfbudget/__init__.py").read()
    ):
        parser.add_argument(
            "--version",
            action="version",
            version=version.group(1),
        )

    subparsers = parser.add_subparsers(required=True)

    # TODO Init
    # init = subparsers.add_parser("init")
    # init.set_defaults(op=Operation.Init)

    # Exports transactions to .csv file
    export = subparsers.add_parser("export")
    export.set_defaults(op=Operation.Export)
    file_options(export)

    pimport = subparsers.add_parser("import")
    pimport.set_defaults(op=Operation.Import)
    pimport.add_argument("file", nargs=1, type=str)

    # Parse from .csv
    parse = subparsers.add_parser("parse")
    parse.set_defaults(op=Operation.Parse)
    parse.add_argument("path", nargs="+", type=str)
    parse.add_argument("--bank", nargs=1, type=str)
    parse.add_argument("--creditcard", nargs=1, type=str)

    # Automatic/manual categorization
    categorize = subparsers.add_parser("categorize").add_subparsers(required=True)
    auto = categorize.add_parser("auto")
    auto.set_defaults(op=Operation.Categorize)
    auto.add_argument("--no-nulls", action="store_false")

    categorize.add_parser("manual").set_defaults(op=Operation.ManualCategorization)

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

    # Banks
    bank(subparsers.add_parser("bank"))

    # PSD2 access token
    subparsers.add_parser("token").set_defaults(op=Operation.Token)

    # PSD2 requisition id
    requisition = subparsers.add_parser("eua")
    requisition.set_defaults(op=Operation.RequisitionId)
    requisition.add_argument("id", nargs=1, type=str)
    requisition.add_argument("country", nargs=1, type=str)

    # Download through the PSD2 API
    download = subparsers.add_parser("download", parents=[period])
    download.set_defaults(op=Operation.Download)
    download_banks = download.add_mutually_exclusive_group()
    download_banks.add_argument("--all", action="store_true")
    download_banks.add_argument("--banks", nargs="+", type=str)
    download.add_argument("--dry-run", action="store_true")

    # List available banks in country C
    banks = subparsers.add_parser("banks")
    banks.set_defaults(op=Operation.PSD2CountryBanks)
    banks.add_argument("country", nargs=1, type=str)

    # Categories
    category(subparsers.add_parser("category"))

    # Tag
    tags(subparsers.add_parser("tag"))

    # Link
    link(subparsers.add_parser("link"))

    return parser


def graph(args):
    """Plots the transactions over a period of time.

    Args:
        args (dict): argparse variables
    """
    start, end = pfbudget.utils.utils.parse_args_period(args)
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
    start, end = pfbudget.utils.utils.parse_args_period(args)
    if args.option == "net":
        pfbudget.reporting.report.net(DatabaseClient(args.database), start, end)
    elif args.option == "detailed":
        pfbudget.reporting.report.detailed(DatabaseClient(args.database), start, end)


def bank(parser: argparse.ArgumentParser):
    commands = parser.add_subparsers(required=True)

    add = commands.add_parser("add")
    add.set_defaults(op=Operation.BankAdd)
    add.add_argument("bank", nargs=1, type=str)
    add.add_argument("bic", nargs=1, type=str)
    add.add_argument("type", nargs=1, type=str, choices=[e.name for e in AccountType])

    rem = commands.add_parser("del")
    rem.set_defaults(op=Operation.BankDel)
    rem.add_argument("bank", nargs="+", type=str)

    mod = commands.add_parser("mod")
    mod.set_defaults(op=Operation.BankMod)
    mod.add_argument("bank", nargs=1, type=str)
    mod.add_argument("--bic", nargs=1, type=str)
    mod.add_argument("--type", nargs=1, type=str, choices=[e.name for e in AccountType])
    mod.add_argument("--remove", nargs="*", default=[], type=str)

    psd2(commands.add_parser("psd2"))

    export = commands.add_parser("export")
    export.set_defaults(op=Operation.ExportBanks)
    file_options(export)

    pimport = commands.add_parser("import")
    pimport.set_defaults(op=Operation.ImportBanks)
    file_options(pimport)


def psd2(parser: argparse.ArgumentParser):
    commands = parser.add_subparsers(required=True)

    add = commands.add_parser("add")
    add.set_defaults(op=Operation.PSD2Add)
    add.add_argument("bank", nargs=1, type=str)
    add.add_argument("--bank_id", nargs=1, type=str)
    add.add_argument("--requisition_id", nargs=1, type=str)
    add.add_argument("--invert", action="store_true")

    rem = commands.add_parser("del")
    rem.set_defaults(op=Operation.PSD2Del)
    rem.add_argument("bank", nargs="+", type=str)

    mod = commands.add_parser("mod")
    mod.set_defaults(op=Operation.PSD2Mod)
    mod.add_argument("bank", nargs=1, type=str)
    mod.add_argument("--bank_id", nargs=1, type=str)
    mod.add_argument("--requisition_id", nargs=1, type=str)
    mod.add_argument("--invert", action="store_true")
    mod.add_argument("--remove", nargs="*", default=[], type=str)


def category(parser: argparse.ArgumentParser):
    commands = parser.add_subparsers(required=True)

    add = commands.add_parser("add")
    add.set_defaults(op=Operation.CategoryAdd)
    add.add_argument("category", nargs="+", type=str)
    add.add_argument("--group", nargs="?", type=str)

    remove = commands.add_parser("remove")
    remove.set_defaults(op=Operation.CategoryRemove)
    remove.add_argument("category", nargs="+", type=str)

    update = commands.add_parser("update")
    update.set_defaults(op=Operation.CategoryUpdate)
    update.add_argument("category", nargs="+", type=str)
    update.add_argument("--group", nargs="?", type=str)

    schedule = commands.add_parser("schedule")
    schedule.set_defaults(op=Operation.CategorySchedule)
    schedule.add_argument("category", nargs="+", type=str)
    schedule.add_argument("period", nargs=1, choices=[e.value for e in Period])
    schedule.add_argument("--frequency", nargs=1, default=[1], type=int)

    rule = commands.add_parser("rule")
    category_rule(rule)

    group = commands.add_parser("group")
    category_group(group)

    export = commands.add_parser("export")
    export.set_defaults(op=Operation.ExportCategories)
    file_options(export)

    pimport = commands.add_parser("import")
    pimport.set_defaults(op=Operation.ImportCategories)
    file_options(pimport)


def category_group(parser: argparse.ArgumentParser):
    commands = parser.add_subparsers(required=True)

    add = commands.add_parser("add")
    add.set_defaults(op=Operation.GroupAdd)
    add.add_argument("group", nargs="+", type=str)

    remove = commands.add_parser("remove")
    remove.set_defaults(op=Operation.GroupRemove)
    remove.add_argument("group", nargs="+", type=str)

    export = commands.add_parser("export")
    export.set_defaults(op=Operation.ExportCategoryGroups)
    file_options(export)

    pimport = commands.add_parser("import")
    pimport.set_defaults(op=Operation.ImportCategoryGroups)
    file_options(pimport)


def category_rule(parser: argparse.ArgumentParser):
    commands = parser.add_subparsers(required=True)

    add = commands.add_parser("add")
    add.set_defaults(op=Operation.RuleAdd)
    add.add_argument("category", nargs="+", type=str)
    rules(add)

    remove = commands.add_parser("remove")
    remove.set_defaults(op=Operation.RuleRemove)
    remove.add_argument("id", nargs="+", type=int)

    modify = commands.add_parser("modify")
    modify.set_defaults(op=Operation.RuleModify)
    modify.add_argument("id", nargs="+", type=int)
    modify.add_argument("--category", nargs=1, type=str)
    rules(modify)
    modify.add_argument("--remove", nargs="*", default=[], type=str)

    export = commands.add_parser("export")
    export.set_defaults(op=Operation.ExportCategoryRules)
    file_options(export)

    pimport = commands.add_parser("import")
    pimport.set_defaults(op=Operation.ImportCategoryRules)
    file_options(pimport)


def tags(parser: argparse.ArgumentParser):
    commands = parser.add_subparsers(required=True)

    add = commands.add_parser("add")
    add.set_defaults(op=Operation.TagAdd)
    add.add_argument("tag", nargs="+", type=str)

    remove = commands.add_parser("remove")
    remove.set_defaults(op=Operation.TagRemove)
    remove.add_argument("tag", nargs="+", type=str)

    rule = commands.add_parser("rule")
    tag_rule(rule)


def tag_rule(parser: argparse.ArgumentParser):
    commands = parser.add_subparsers(required=True)

    add = commands.add_parser("add")
    add.set_defaults(op=Operation.TagRuleAdd)
    add.add_argument("tag", nargs="+", type=str)
    rules(add)

    remove = commands.add_parser("remove")
    remove.set_defaults(op=Operation.TagRuleRemove)
    remove.add_argument("id", nargs="+", type=int)

    modify = commands.add_parser("modify")
    modify.set_defaults(op=Operation.TagRuleModify)
    modify.add_argument("id", nargs="+", type=int)
    modify.add_argument("--tag", nargs=1, type=str)
    rules(modify)

    export = commands.add_parser("export")
    export.set_defaults(op=Operation.ExportTagRules)
    file_options(export)

    pimport = commands.add_parser("import")
    pimport.set_defaults(op=Operation.ImportTagRules)
    file_options(pimport)


def rules(parser: argparse.ArgumentParser):
    parser.add_argument("--start", nargs=1, type=dt.date.fromisoformat)
    parser.add_argument("--end", nargs=1, type=dt.date.fromisoformat)
    parser.add_argument("--description", nargs=1, type=str)
    parser.add_argument("--regex", nargs=1, type=str)
    parser.add_argument("--bank", nargs=1, type=str)
    parser.add_argument("--min", nargs=1, type=decimal.Decimal)
    parser.add_argument("--max", nargs=1, type=decimal.Decimal)


def link(parser: argparse.ArgumentParser):
    commands = parser.add_subparsers(required=True)

    forge = commands.add_parser("forge")
    forge.set_defaults(op=Operation.Forge)
    forge.add_argument("original", nargs=1, type=int)
    forge.add_argument("links", nargs="+", type=int)

    dismantle = commands.add_parser("dismantle")
    dismantle.set_defaults(op=Operation.Dismantle)
    dismantle.add_argument("original", nargs=1, type=int)
    dismantle.add_argument("links", nargs="+", type=int)


def file_options(parser: argparse.ArgumentParser):
    parser.add_argument("file", nargs=1, type=str)
    parser.add_argument("format", nargs=1, default="pickle")
