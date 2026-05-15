import datetime as dt
from decimal import Decimal
from pathlib import Path

from pfbudget.db.model import BankTransaction, MoneyTransaction
from pfbudget.export.ofx import export
from tests.mocks.transactions import bank, money, simple


class TestOFXExport:
    def test_creates_file(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(simple, out)
        assert out.exists()

    def test_ofx_header(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(simple, out)
        content = out.read_text()
        assert "OFXHEADER:100" in content
        assert "<OFX>" in content
        assert "<STMTTRNRS>" in content

    def test_transaction_fields(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        transactions = [
            BankTransaction(
                dt.date(2024, 3, 15), "Coffee shop", Decimal("-4.50"), bank="mybank"
            ),
        ]
        transactions[0].id = 42
        export(transactions, out)
        content = out.read_text()
        assert "<DTPOSTED>20240315" in content
        assert "<TRNAMT>-4.50" in content
        assert "<FITID>42" in content
        assert "<MEMO>Coffee shop" in content
        assert "<BANKID>mybank" in content

    def test_credit_trntype(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        t = BankTransaction(dt.date(2024, 1, 1), "Salary", Decimal("1000.00"), bank="b")
        t.id = 1
        export([t], out)
        assert "<TRNTYPE>CREDIT" in out.read_text()

    def test_debit_trntype(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        t = BankTransaction(dt.date(2024, 1, 1), "Rent", Decimal("-800.00"), bank="b")
        t.id = 2
        export([t], out)
        assert "<TRNTYPE>DEBIT" in out.read_text()

    def test_date_range(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(simple, out)
        content = out.read_text()
        assert "<DTSTART>20230114" in content
        assert "<DTEND>20230214" in content

    def test_account_id(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(simple, out, account_id="PT50000201231234567890154")
        assert "<ACCTID>PT50000201231234567890154" in out.read_text()

    def test_empty_transactions(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export([], out)
        content = out.read_text()
        assert "<OFX>" in content
        assert "<STMTTRN>" not in content

    def test_no_memo_when_description_none(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        t = BankTransaction(dt.date(2024, 1, 1), None, Decimal("-10.00"), bank="b")
        t.id = 3
        export([t], out)
        assert "<MEMO>" not in out.read_text()

    def test_no_bankid_for_money_transaction(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        t = MoneyTransaction(dt.date(2024, 1, 1), "Cash", Decimal("-20.00"))
        t.id = 4
        export([t], out)
        assert "<BANKID>" not in out.read_text()

    def test_multiple_transactions(self, tmp_path: Path):
        out = tmp_path / "out.ofx"
        export(bank + money, out)
        assert out.read_text().count("<STMTTRN>") == len(bank) + len(money)
