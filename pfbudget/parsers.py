from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .transactions import Transaction


class Parser:
    def parse(self, file):
        pass

    @staticmethod
    def parse_csv(file: Path, append=False):
        name = file.stem.split("_")
        try:
            bank, _ = name[0], int(name[1])
        except ValueError:
            _, bank = int(name[0]), name[1]

        p = dict(
            Bank1=Bank1,
            Bank2=Bank2,
            Bank2CC=Bank2CC,
            BANK3=Bank3,
        )

        try:
            parser = p[bank]()
        except KeyError as e:
            print(f"{e} {bank} parser doesnt exist. Cant parse {name}")
            return

        transactions = parser.parse(file)
        return transactions


class Bank1(Parser):
    """Bank 1 parser

    Bank 1 transcripts have the following properties:
    encoding: utf-8
    separator: ;
    starting line: 5
    date format: %d/%m/%Y

    The reading order is reversed to go from earlier to latest.
    """

    encoding = "utf-8"
    separator = ";"

    def parse(self, file):
        transactions = []
        reader = [
            line.rstrip().split(self.separator)
            for line in open(file, encoding=self.encoding)
        ][5:]

        for transaction in reversed(reader):
            transaction = [field.rstrip() for field in transaction]
            date = datetime.strptime(transaction[1], "%d/%m/%Y").date()
            description = " ".join(transaction[3].split())
            value = Decimal(transaction[4])

            transactions.append(
                Transaction(date.isoformat(), description, "Bank1", value)
            )

        return transactions


class Bank2(Parser):
    """Bank 2 parser

    Bank 2 transcripts have the following properties:
    encoding: utf-8
    separator: tab
    date format: %d/%m/%Y or %d-%m-%Y
    decimal separator: ,
    """

    encoding = "utf-8"
    separator = "\t"

    def parse(self, file):
        transactions = []
        reader = [
            line.rstrip().split(self.separator)
            for line in open(file, encoding=self.encoding)
        ]

        for transaction in reader:
            try:
                date = datetime.strptime(transaction[0], "%d/%m/%Y").date()
            except ValueError:  # date can differ due to locales
                date = datetime.strptime(transaction[0], "%d-%m-%Y").date()
            description = transaction[2]

            # works for US and EU locales (5,000.00 and 5 000,00)
            value = list(transaction[3].replace("\xa0", ""))  # non-breaking space
            value[-3] = "."
            value = "".join(value)
            value = value.replace(",", "")
            value = Decimal(value)

            transactions.append(
                Transaction(date.isoformat(), description, "Bank2", value)
            )

        return transactions


class Bank2CC(Parser):
    """Bank 2 credit card parser

    Bank 2 credit card transcripts have the following properties:
    encoding: utf-8
    separator: tab
    date format: %d/%m/%Y or %d-%m-%Y
    decimal separator: ,
    """

    encoding = "utf-8"
    separator = "\t"

    def parse(self, file):
        transactions = []
        reader = [
            line.rstrip().split(self.separator)
            for line in open(file, encoding=self.encoding)
        ]

        for transaction in reader:
            try:
                date = datetime.strptime(transaction[0], "%d/%m/%Y").date()
            except ValueError:  # date can differ due to locales
                date = datetime.strptime(transaction[0], "%d-%m-%Y").date()
            description = transaction[2]

            # works for US and EU locales (5,000.00 and 5 000,00)
            value = list(transaction[3].replace("\xa0", ""))  # non-breaking space
            value[-3] = "."
            value = "".join(value)
            value = value.replace(",", "")
            value = Decimal(value)

            if value > 0:
                date = datetime.strptime(transaction[1], "%d/%m/%Y").date()

            transactions.append(
                Transaction(date.isoformat(), description, "Bank2CC", value)
            )

        return transactions


class Bank3(Parser):
    """Bank 3 parser

    Bank 3 transcripts have the following properties:
    encoding: windows-1252 (passed as argument)
    separator: ;
    starting line: 7
    finishing line: -1
    date format: %d-%m-%Y
    decimal separator: ,
    thousands separator: .

    Bank 3 has credits in a different column from debits. These also have to be
    negated. The reading order is reversed to go from earlier to latest.
    """

    encoding = "windows-1252"
    separator = ","

    def parse(self, file):
        transactions = []
        reader = [
            line.rstrip().split(self.separator)
            for line in open(file, encoding=self.encoding)
        ][7:-1]

        for transaction in reversed(reader):
            transaction = [field.rstrip() for field in transaction]
            date = datetime.strptime(transaction[1], "%d-%m-%Y").date()
            description = transaction[2]
            if t := transaction[3]:
                t = t.replace(".", "").replace(",", ".")
                value = -Decimal(t)
            else:
                t = transaction[4].replace(".", "").replace(",", ".")
                value = Decimal(t)

            transactions.append(
                Transaction(date.isoformat(), description, "Bank3", value)
            )

        return transactions
