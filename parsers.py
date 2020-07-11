from datetime import datetime
from decimal import Decimal, InvalidOperation


class Parser:
    @staticmethod
    def get_transactions(file, encoding, sep="\t"):
        with open(file, newline="", encoding=encoding) as f:
            transactions = [line.rstrip().split(sep) for line in f]

        return transactions

    def parse(self, file, encoding="utf-8"):
        pass


class Bank1(Parser):
    """Bank 1 parser

    Bank 1 transcripts have the following properties:
    encoding: utf-8
    separator: ;
    starting line: 5
    date format: %d/%m/%Y
    """

    def parse(self, file, encoding="utf-8"):
        transactions = []

        for transaction in self.get_transactions(file, encoding, sep=";")[5:]:
            transaction = [field.rstrip() for field in transaction]
            date = datetime.strptime(transaction[1], "%d/%m/%Y").date()
            description = " ".join(transaction[3].split())
            value = Decimal(transaction[4])

            transactions.append([date.isoformat(), description, "Bank1", value])

        return transactions


class Bank2(Parser):
    """Bank 2 parser

    Bank 2 transcripts have the following properties:
    encoding: utf-8
    separator: tab
    date format: %d/%m/%Y
    decimal separator: ,

    Bank 2 also has an associated credit card, for which the transaction value
    has to be negated.
    """

    def __init__(self, cc=False):
        self.cc = cc

    def parse(self, file, encoding="utf-8"):
        transactions = []

        for transaction in self.get_transactions(file, encoding):
            date = datetime.strptime(transaction[0], "%d/%m/%Y").date()
            description = transaction[2]
            try:
                value = Decimal(transaction[3])
            except InvalidOperation:
                transaction[3] = transaction[3].replace(",", "")
                value = Decimal(transaction[3])

            if not self.cc:
                card = "Bank2"
            else:
                value = -value
                card = "Bank2 CC"

            transactions.append([date.isoformat(), description, card, value])

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
    negated.
    """

    def parse(self, file, encoding="utf-8"):
        transactions = []

        for transaction in self.get_transactions(file, encoding, sep=";")[7:-1]:
            transaction = [field.rstrip() for field in transaction]
            date = datetime.strptime(transaction[1], "%d-%m-%Y").date()
            description = transaction[2]
            if t := transaction[3]:
                t = t.replace(".", "").replace(",", ".")
                value = -Decimal(t)
            else:
                t = transaction[4].replace(".", "").replace(",", ".")
                value = Decimal(t)

            transactions.append([date.isoformat(), description, "Bank3", value])

        return transactions
