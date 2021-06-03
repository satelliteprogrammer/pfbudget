from decimal import Decimal
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
    s = s.strip().replace(u"\xa0", "").replace(" ", "")
    s = s.strip().replace("€", "").replace("+", "")
    if s.rfind(",") > s.rfind("."):
        s = s.replace(".", "")
        i = s.rfind(",")
        li = list(s)
        li[i] = "."
        s = "".join(li)
    return Decimal(s.replace(",", ""))


def find_credit_institution(fn, banks, creditcards):
    name = Path(fn).stem.split("_")
    bank, cc = None, None
    for i in name:
        try:
            int(i)
        except ValueError:
            if not bank:
                bank = i
            else:
                cc = i

    if not bank:
        raise WrongFilenameError

    if bank not in banks:
        raise BankNotAvailableError
    if cc and cc not in creditcards:
        raise CreditCardNotAvailableError

    return bank, cc
