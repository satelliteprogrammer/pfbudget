from datetime import datetime
from decimal import Decimal
import csv
import os

from parsers import Bank1, Bank2, Bank3, Parser


def write_transactions(file, transactions, append=False):
    with open(file, "a" if append else "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerows(transactions)


def parse(parser: Parser, input, output, reverse=True, encoding="utf-8"):
    transactions = parser.parse(input, encoding)
    if reverse:
        transactions.reverse()
    write_transactions(output, transactions)

# parse(Bank1(), ".rawdata/Bank1_2019.csv", "data/2019_Bank1.csv")
# parse(Bank2(), ".rawdata/Bank2_2020.csv", "data/2020_Bank2.csv", reverse=False)
# parse(Bank2(cc=True), ".rawdata/Bank2CC_2020.csv", "data/2020_Bank2CC.csv", reverse=False)
# parse(Bank3(), ".rawdata/Bank3_2019.csv", "data/2019_Bank3.csv", encoding="windows-1252")
