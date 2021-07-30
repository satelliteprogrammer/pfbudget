from __future__ import annotations
from collections import namedtuple
from decimal import Decimal
from importlib import import_module
from typing import TYPE_CHECKING
import datetime as dt
import yaml

from .transactions import Transaction
from . import utils

if TYPE_CHECKING:
    from .database import DBManager

Index = namedtuple(
    "Index", ["date", "text", "value", "negate"], defaults=[-1, -1, -1, False]
)
Options = namedtuple(
    "Options",
    [
        "encoding",
        "separator",
        "date_fmt",
        "start",
        "end",
        "debit",
        "credit",
        "additional_parser",
        "category",
        "VISA",
        "MasterCard",
        "AmericanExpress",
    ],
    defaults=[
        "",
        "",
        "",
        1,
        None,
        Index(),
        Index(),
        False,
        None,
        None,
        None,
        None,
    ],
)


def parse_data(db: DBManager, filename: str, args: dict) -> None:
    cfg: dict = yaml.safe_load(open("parsers.yaml"))
    assert (
        "Banks" in cfg
    ), "parsers.yaml is missing the Banks section with the list of available banks"

    if not args["bank"]:
        bank, creditcard = utils.find_credit_institution(
            filename, cfg.get("Banks"), cfg.get("CreditCards")
        )
    else:
        bank = args["bank"][0]
        creditcard = None if not args["creditcard"] else args["creditcard"][0]

    if not creditcard:
        options: dict = cfg[bank]
    else:
        options: dict = cfg[bank][creditcard]
        bank += creditcard

    if args["category"]:
        options["category"] = args["category"][0]

    if options.get("additional_parser"):
        parser = getattr(import_module("pfbudget.parsers"), bank)
        transactions = parser(filename, bank, options).parse()
    else:
        transactions = Parser(filename, bank, options).parse()

    db.insert_transactions(transactions)


class Parser:
    def __init__(self, filename: str, bank: str, options: dict):
        self.filename = filename
        self.bank = bank

        if debit := options.get("debit", None):
            options["debit"] = Index(**debit)
        if credit := options.get("credit", None):
            options["credit"] = Index(**credit)

        self.options = Options(**options)

    def func(self, transaction: Transaction):
        pass

    def parse(self) -> list[Transaction]:
        transactions = [
            Parser.transaction(line, self.bank, self.options, self.func)
            for line in list(open(self.filename, encoding=self.options.encoding))[
                self.options.start - 1 : self.options.end
            ]
            if len(line) > 2
        ]
        return transactions

    @staticmethod
    def index(line: list, options: Options) -> Index:
        if options.debit.date != -1 and options.credit.date != -1:
            if options.debit.value != options.credit.value:
                if line[options.debit.value]:
                    index = options.debit
                elif line[options.credit.value]:
                    index = options.credit
            elif options.debit.date != options.credit.date:
                negate = 1 if (options.debit.negate or options.credit.negate) else -1
                if (negate * utils.parse_decimal(line[options.debit.value])) < 0:
                    index = options.debit
                else:
                    index = options.credit
            elif options.debit.text != options.credit.text:
                if line[options.debit.text]:
                    index = options.debit
                elif line[options.credit.text]:
                    index = options.credit
            else:
                raise IndexError("Debit and credit indexes are equal")
        elif options.debit.date != -1:
            index = options.debit
        elif options.credit.date != -1:
            index = options.credit
        else:
            raise IndexError("No debit not credit indexes available")

        return index

    @staticmethod
    def transaction(line: str, bank: str, options: Options, func) -> Transaction:
        line = line.rstrip().split(options.separator)
        index = Parser.index(line, options)

        date = (
            dt.datetime.strptime(line[index.date].strip(), options.date_fmt)
            .date()
            .isoformat()
        )
        text = line[index.text]
        value = utils.parse_decimal(line[index.value])
        if index.negate:
            value = -value

        if options.category:
            category = line[options.category]
            transaction = Transaction(date, text, bank, value, category)
        else:
            transaction = Transaction(date, text, bank, value, options.category)

        if options.additional_parser:
            func(transaction)
        return transaction


class Bank1(Parser):
    def __init__(self, filename: str, bank: str, options: dict):
        super().__init__(filename, bank, options)
        self.transfers = []
        self.transaction_cost = -Decimal("1")

    def func(self, transaction: Transaction):
        if "transf" in transaction.description.lower() and transaction.value < 0:
            transaction.value -= self.transaction_cost
            self.transfers.append(transaction.date)

    def parse(self) -> list:
        transactions = super().parse()
        for date in self.transfers:
            transactions.append(
                Transaction(date, "Transaction cost", self.bank, self.transaction_cost)
            )
        return transactions
