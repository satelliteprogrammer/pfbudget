from pathlib import Path
import argparse
import datetime as dt

from .graph import average, discrete, monthly
from .state import pfstate
from .transactions import load_transactions, save_transactions
from . import report
from . import tools


class PfBudgetInitialized(Exception):
    pass


class PfBudgetNotInitialized(Exception):
    pass


class DataFileMissing(Exception):
    pass


def get_argparser():
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

    p_restart.add_argument("--raw", help="new raw data dir")
    p_restart.add_argument("--data", help="new parsed data dir")

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

    p_init.set_defaults(func=init)
    p_restart.set_defaults(func=restart)
    p_backup.set_defaults(func=backup)
    p_parse.set_defaults(func=parse)
    p_vacation.set_defaults(func=vacation)
    p_status.set_defaults(func=status)
    p_graph.set_defaults(func=graph)
    p_report.set_defaults(func=f_report)

    return parser


def init(state, args):
    """Initialization

    Creates the state file which stores the internal state of the program
    for later use.
    Calls parse, that parses all raw files into the data directory.

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    Raises:
        PfBudgetInitialized: Raised when there's already an initialized state
    """
    if not state:
        s = dict(
            filename=tools.STATE_FILE,
            raw_dir=args.raw,
            data_dir=args.data,
            raw_files=[],
            data_files=[],
            vacations=[],
            last_backup="",
            last_datadir_backup="",
        )
        try:
            state = pfstate(tools.STATE_FILE, s)
            parse(state, args)
        except Exception as e:
            print(e)
            if Path(tools.STATE_FILE).is_file():
                print(f"Deleting {tools.STATE_FILE}")
                Path(tools.STATE_FILE).unlink()

    else:
        raise PfBudgetInitialized(f"{Path(tools.STATE_FILE)} already exists")


def restart(state, args):
    """Restart

    Deletes state and creates a new one.
    Parses all raw files into the data directory. New dirs can be passed as
    arguments, otherwise uses previous values.

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables

    Raises:
        DataFileMissing: Missing data files from those listed in state
        PfBudgetNotInitialized: Raised when no state has been initialized yet
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
        raise PfBudgetNotInitialized(f"{Path(tools.STATE_FILE)} doesn't exist")


def backup(state, args):
    """Backup

    Saves all transactions on transactions_#.csv

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    """
    if args.option == "single":
        tools.backup(state)
    elif args.option == "all":
        tools.full_backup(state)
    elif args.option == "restore":
        tools.restore(state)


def parse(state, args):
    """Parser

    Parses the contents of the raw directory into the data files, and
    categorizes the transactions.

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    """
    raw_dir = args.raw if hasattr(args, "raw") else None
    data_dir = args.data if hasattr(args, "data") else None

    tools.parser(state, raw_dir, data_dir)
    categorize(state, args)


def categorize(state, args):
    """Categorization

    Automatically categorizes transactions based on the regex of each
    category. Manually present the remaining to the user.

    Args:
        state (PFState): Internal state of the program
        args (dict): argparse variables
    """
    transactions = load_transactions(state.data_dir)
    missing = tools.auto_categorization(state, transactions)
    if missing:
        tools.manual_categorization(state, transactions)
    save_transactions(state.data_dir, transactions)


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
    parser = get_argparser()
    args = parser.parse_args()

    state = pfstate(tools.STATE_FILE)
    args.func(state, args)
