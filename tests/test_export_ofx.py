import datetime as dt
from decimal import Decimal
from pathlib import Path
import xml.etree.ElementTree as ET

from pfbudget.db.model import BankTransaction, MoneyTransaction
from pfbudget.export.ofx import export
from tests.mocks.transactions import bank, money, simple


def _parse(path: Path) -> ET.Element:
    # Strip the two processing instructions before parsing
    lines = path.read_text(encoding="utf-8").splitlines()
    xml_lines = [l for l in lines if not l.startswith("<?")]
    return ET.fromstring("\n".join(xml_lines))


class TestOFXExport:
    def test_creates_file(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(simple, out)
        assert out.exists()

    def test_ofx_header(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(simple, out)
        content = out.read_text()
        assert '<?xml version="1.0"' in content
        assert 'VERSION="230"' in content
        assert "<OFX>" in content
        assert "<STMTTRNRS>" in content

    def test_valid_xml(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(simple, out)
        root = _parse(out)
        assert root.tag == "OFX"

    def test_transaction_fields(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        t = BankTransaction(dt.date(2024, 3, 15), "Coffee shop", Decimal("-4.50"), bank="mybank")
        t.id = 42
        export([t], out)
        root = _parse(out)
        stmttrn = root.find(".//STMTTRN")
        assert stmttrn is not None
        assert stmttrn.findtext("DTPOSTED") == "20240315"
        assert stmttrn.findtext("TRNAMT") == "-4.50"
        assert stmttrn.findtext("FITID") == "42"
        assert stmttrn.findtext("MEMO") == "Coffee shop"
        assert stmttrn.findtext("BANKID") == "mybank"

    def test_credit_trntype(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        t = BankTransaction(dt.date(2024, 1, 1), "Salary", Decimal("1000.00"), bank="b")
        t.id = 1
        export([t], out)
        assert _parse(out).findtext(".//TRNTYPE") == "CREDIT"

    def test_debit_trntype(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        t = BankTransaction(dt.date(2024, 1, 1), "Rent", Decimal("-800.00"), bank="b")
        t.id = 2
        export([t], out)
        assert _parse(out).findtext(".//TRNTYPE") == "DEBIT"

    def test_date_range(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(simple, out)
        root = _parse(out)
        assert root.findtext(".//DTSTART") == "20230114"
        assert root.findtext(".//DTEND") == "20230214"

    def test_account_id(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(simple, out, account_id="PT50000201231234567890154")
        assert _parse(out).findtext(".//ACCTID") == "PT50000201231234567890154"

    def test_empty_transactions(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export([], out)
        root = _parse(out)
        assert root.tag == "OFX"
        assert root.find(".//STMTTRN") is None

    def test_no_memo_when_description_none(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        t = BankTransaction(dt.date(2024, 1, 1), None, Decimal("-10.00"), bank="b")
        t.id = 3
        export([t], out)
        assert _parse(out).find(".//MEMO") is None

    def test_no_bankid_for_money_transaction(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        t = MoneyTransaction(dt.date(2024, 1, 1), "Cash", Decimal("-20.00"))
        t.id = 4
        export([t], out)
        assert _parse(out).find(".//BANKID") is None

    def test_multiple_transactions(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(bank + money, out)
        assert len(_parse(out).findall(".//STMTTRN")) == len(bank) + len(money)

    def test_filter_by_bank(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(bank, out, banks=["bank#1"])
        stmttrns = _parse(out).findall(".//STMTTRN")
        assert len(stmttrns) == 1
        assert stmttrns[0].findtext("BANKID") == "bank#1"

    def test_filter_by_multiple_banks(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(bank, out, banks=["bank#1", "bank#2"])
        assert len(_parse(out).findall(".//STMTTRN")) == 2

    def test_filter_excludes_non_bank_transactions(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(bank + money, out, banks=["bank#1"])
        assert len(_parse(out).findall(".//STMTTRN")) == 1
