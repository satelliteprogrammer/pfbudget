from __future__ import annotations
import datetime as dt
from collections.abc import Sequence
from pathlib import Path
import xml.etree.ElementTree as ET

from pfbudget.db.model import BankTransaction, Transaction


_OFX_DATE_FMT = "%Y%m%d"

_OFX_PROCESSING_INSTRUCTION = (
    '<?OFX OFXHEADER="200" VERSION="230" SECURITY="NONE"'
    ' OLDFILEUID="NONE" NEWFILEUID="NONE"?>'
)


def _trntype(amount: object) -> str:
    return "CREDIT" if float(str(amount)) >= 0 else "DEBIT"


def _ofx_date(d: dt.date) -> str:
    return d.strftime(_OFX_DATE_FMT)


def _sub(parent: ET.Element, tag: str, text: str) -> ET.Element:
    el = ET.SubElement(parent, tag)
    el.text = text
    return el


def export(
    transactions: Sequence[Transaction],
    path: Path,
    account_id: str = "",
    banks: Sequence[str] = (),
) -> None:
    if banks:
        transactions = [
            t for t in transactions
            if isinstance(t, BankTransaction) and t.bank in banks
        ]
    ofx = ET.Element("OFX")

    msgsrs = ET.SubElement(ofx, "BANKMSGSRSV1")
    stmttrnrs = ET.SubElement(msgsrs, "STMTTRNRS")
    _sub(stmttrnrs, "TRNUID", "1001")
    status = ET.SubElement(stmttrnrs, "STATUS")
    _sub(status, "CODE", "0")
    _sub(status, "SEVERITY", "INFO")

    stmtrs = ET.SubElement(stmttrnrs, "STMTRS")
    _sub(stmtrs, "CURDEF", "EUR")
    acctfrom = ET.SubElement(stmtrs, "BANKACCTFROM")
    _sub(acctfrom, "ACCTID", account_id)
    _sub(acctfrom, "ACCTTYPE", "CHECKING")

    tranlist = ET.SubElement(stmtrs, "BANKTRANLIST")
    if transactions:
        dates = [t.date for t in transactions]
        _sub(tranlist, "DTSTART", _ofx_date(min(dates)))
        _sub(tranlist, "DTEND", _ofx_date(max(dates)))

    for t in transactions:
        stmttrn = ET.SubElement(tranlist, "STMTTRN")
        _sub(stmttrn, "TRNTYPE", _trntype(t.amount))
        _sub(stmttrn, "DTPOSTED", _ofx_date(t.date))
        _sub(stmttrn, "TRNAMT", str(t.amount))
        _sub(stmttrn, "FITID", str(t.id))
        if t.description:
            _sub(stmttrn, "MEMO", t.description)
        if isinstance(t, BankTransaction) and t.bank:
            _sub(stmttrn, "BANKID", t.bank)

    ET.indent(ofx)
    xml_body = ET.tostring(ofx, encoding="unicode", xml_declaration=False)
    path.write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n{_OFX_PROCESSING_INSTRUCTION}\n{xml_body}\n',
        encoding="utf-8",
    )
