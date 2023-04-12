from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path


class WrongFilenameError(Exception):
    pass


class BankNotAvailableError(Exception):
    pass


class CreditCardNotAvailableError(Exception):
    pass


def parse_decimal(s: str) -> Decimal:
    try:
        float(s)
        return Decimal(s)
    except ValueError:
        pass
    try:
        d = s.strip().replace("\xa0", "").replace(" ", "")
        d = d.replace("€", "").replace("+", "").replace("EUR", "").strip()
        if d.rfind(",") > d.rfind("."):
            d = d.replace(".", "")
            i = d.rfind(",")
            li = list(d)
            li[i] = "."
            d = "".join(li)
        return Decimal(d.replace(",", ""))
    except InvalidOperation:
        raise InvalidOperation(f"{s} -> {d}")


def find_credit_institution(fn, banks, creditcards):
    name = Path(fn).stem.split("_")
    bank, cc = None, None
    for i in name:
        try:
            int(i)
        except ValueError:
            if not bank:
                bank = i
            elif not cc:
                cc = i

    if not bank:
        raise WrongFilenameError

    if bank.lower() not in [bank.lower() for bank in banks]:
        raise BankNotAvailableError(f"{fn} -> {bank}: {banks}")
    if cc and cc.lower() not in [cc.lower() for cc in creditcards]:
        print(f"{fn} -> {cc} not in {creditcards}, using {bank} parser")
        cc = None

    return bank, cc


def parse_args_period(args: dict):
    start, end = date.min, date.max
    if args["start"]:
        start = datetime.strptime(args["start"][0], "%Y/%m/%d").date()

    if args["end"]:
        end = datetime.strptime(args["end"][0], "%Y/%m/%d").date()

    if args["interval"]:
        start = datetime.strptime(args["interval"][0], "%Y/%m/%d").date()
        end = datetime.strptime(args["interval"][1], "%Y/%m/%d").date()

    if args["year"]:
        start = datetime.strptime(args["year"][0], "%Y").date()
        end = datetime.strptime(str(int(args["year"][0]) + 1), "%Y").date() - timedelta(
            days=1
        )

    return start, end
