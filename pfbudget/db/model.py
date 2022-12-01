from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    MetaData,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, MappedAsDataclass

from decimal import Decimal
from typing import Annotated, Optional
import datetime as dt
import enum


class Base(MappedAsDataclass, DeclarativeBase):
    __table_args__ = {"schema": "transactions"}
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class AccountType(enum.Enum):
    checking = enum.auto()
    savings = enum.auto()
    investment = enum.auto()
    VISA = enum.auto()
    MASTERCARD = enum.auto()


accounttype = Annotated[
    AccountType,
    mapped_column(Enum(AccountType, inherit_schema=True)),
]


class Bank(Base):
    __tablename__ = "banks"

    name: Mapped[str] = mapped_column(unique=True)
    BIC: Mapped[str] = mapped_column(String(8), primary_key=True)
    type: Mapped[accounttype] = mapped_column(primary_key=True)


bankfk = Annotated[str, mapped_column(Text, ForeignKey(Bank.name))]

idpk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
money = Annotated[Decimal, mapped_column(Numeric(16, 2), nullable=False)]


class Original(Base):
    __tablename__ = "originals"

    id: Mapped[idpk] = mapped_column(autoincrement=True)
    date: Mapped[dt.date]
    description: Mapped[Optional[str]]
    bank: Mapped[bankfk]
    amount: Mapped[money]


idfk = Annotated[int, mapped_column(BigInteger, ForeignKey(Original.id))]


class Categorized(Base):
    __tablename__ = "categorized"

    id: Mapped[idfk] = mapped_column(primary_key=True)
    category: Mapped[str]


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[idfk] = mapped_column(primary_key=True)
    note: Mapped[str]


class Nordigen(Base):
    __tablename__ = "nordigen"

    name: Mapped[bankfk] = mapped_column(primary_key=True)
    bank_id: Mapped[Optional[str]]
    requisition_id: Mapped[Optional[str]]
    invert: Mapped[Optional[bool]]


class Tags(Base):
    __tablename__ = "tags"

    id: Mapped[idfk] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(primary_key=True)
