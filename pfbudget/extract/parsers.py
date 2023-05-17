from __future__ import annotations
from decimal import Decimal
from importlib import import_module
from pathlib import Path
import datetime as dt
from typing import Any, Callable, NamedTuple, Optional
import yaml

from pfbudget.common.types import NoBankSelected
from pfbudget.db.model import BankTransaction
from pfbudget.utils import utils


class Index(NamedTuple):
    date: int = -1
    text: int = -1
    value: int = -1
    negate: bool = False


class Options(NamedTuple):
    encoding: str
    separator: str
    date_fmt: str
    start: int = 1
    end: Optional[int] = None
    debit: Index = Index()
    credit: Index = Index()
    additional_parser: bool = False
    VISA: Optional[Options] = None
    MasterCard: Optional[Options] = None
    AmericanExpress: Optional[Options] = None


def parse_data(filename: Path, args: dict[str, Any]) -> list[BankTransaction]:
    cfg: dict[str, Any] = yaml.safe_load(open("parsers.yaml"))
    assert (
        "Banks" in cfg
    ), "parsers.yaml is missing the Banks section with the list of available banks"

    if not args["bank"]:
        bank, creditcard = utils.find_credit_institution(  # type: ignore
            filename, cfg.get("Banks"), cfg.get("CreditCards")
        )
    else:
        bank = args["bank"][0]
        creditcard = None if not args["creditcard"] else args["creditcard"][0]

    try:
        options: dict[str, Any] = cfg[bank]
    except KeyError as e:
        banks = cfg["Banks"]
        raise NoBankSelected(f"{e} not a valid bank, try one of {banks}")

    if creditcard:
        try:
            options = options[creditcard]
        except KeyError as e:
            creditcards = cfg["CreditCards"]
            raise NoBankSelected(f"{e} not a valid bank, try one of {creditcards}")
        bank += creditcard

    if options.get("additional_parser"):
        parser = getattr(import_module("pfbudget.extract.parsers"), bank)
        transactions = parser(filename, bank, options).parse()
    else:
        transactions = Parser(filename, bank, options).parse()

    return transactions


class Parser:
    def __init__(self, filename: Path, bank: str, options: dict[str, Any]):
        self.filename = filename
        self.bank = bank

        if debit := options.get("debit", None):
            options["debit"] = Index(**debit)
        if credit := options.get("credit", None):
            options["credit"] = Index(**credit)

        self.options = Options(**options)

    def func(self, transaction: BankTransaction):
        pass

    def parse(self) -> list[BankTransaction]:
        transactions = [
            Parser.transaction(line, self.bank, self.options, self.func)
            for line in list(open(self.filename, encoding=self.options.encoding))[
                self.options.start - 1 : self.options.end
            ]
            if len(line) > 2
        ]
        return transactions

    @staticmethod
    def index(line: list[str], options: Options) -> Index:
        index = None
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

        return index if index else Index()

    @staticmethod
    def transaction(
        line_: str, bank: str, options: Options, func: Callable[[BankTransaction], None]
    ) -> BankTransaction:
        line = line_.rstrip().split(options.separator)
        index = Parser.index(line, options)

        date = dt.datetime.strptime(line[index.date].strip(), options.date_fmt).date()
        text = line[index.text]
        value = utils.parse_decimal(line[index.value])
        if index.negate:
            value = -value

        transaction = BankTransaction(date, text, value, bank=bank)

        if options.additional_parser:
            func(transaction)
        return transaction


class Bank1(Parser):
    def __init__(self, filename: Path, bank: str, options: dict[str, Any]):
        super().__init__(filename, bank, options)
        self.transfers: list[dt.date] = []
        self.transaction_cost = -Decimal("1")

    def func(self, transaction: BankTransaction):
        if (
            transaction.description
            and "transf" in transaction.description.lower()
            and transaction.amount < 0
        ):
            transaction.amount -= self.transaction_cost
            self.transfers.append(transaction.date)

    def parse(self) -> list[BankTransaction]:
        transactions = super().parse()
        for date in self.transfers:
            transactions.append(
                BankTransaction(
                    date, "Transaction cost", self.transaction_cost, bank=self.bank
                )
            )
        return transactions
