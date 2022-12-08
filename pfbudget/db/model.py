from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    MetaData,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from decimal import Decimal
from typing import Annotated, Optional
import datetime as dt
import enum


class Base(DeclarativeBase):
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
    mealcard = enum.auto()
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

    nordigen: Mapped[Optional[Nordigen]] = relationship(
        back_populates="bank", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"Bank(name={self.name}, BIC={self.BIC}, type={self.type}, nordigen={self.nordigen})"


bankfk = Annotated[str, mapped_column(Text, ForeignKey(Bank.name))]

idpk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
money = Annotated[Decimal, mapped_column(Numeric(16, 2), nullable=False)]


class Transaction(Base):
    __tablename__ = "originals"

    id: Mapped[idpk] = mapped_column(autoincrement=True)
    date: Mapped[dt.date]
    description: Mapped[Optional[str]]
    bank: Mapped[bankfk]
    amount: Mapped[money]

    category: Mapped[Optional[TransactionCategory]] = relationship(
        back_populates="original", lazy="joined"
    )
    note: Mapped[Optional[Note]] = relationship(back_populates="original")
    tags: Mapped[Optional[set[Tag]]] = relationship(
        back_populates="original", cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"Transaction(date={self.date}, description={self.description}, bank={self.bank}, amount={self.amount}, category={self.category})"


idfk = Annotated[
    int, mapped_column(BigInteger, ForeignKey(Transaction.id, ondelete="CASCADE"))
]


class CategoryGroup(Base):
    __tablename__ = "categories_groups"

    name: Mapped[str] = mapped_column(primary_key=True)


class Category(Base):
    __tablename__ = "categories_available"

    name: Mapped[str] = mapped_column(primary_key=True)
    group: Mapped[Optional[str]] = mapped_column(ForeignKey(CategoryGroup.name))

    rules: Mapped[Optional[set[CategoryRule]]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:
        return (
            f"Category(name={self.name}, group={self.group}, #rules={len(self.rules)})"
        )


class TransactionCategory(Base):
    __tablename__ = "categorized"

    id: Mapped[idfk] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(ForeignKey(Category.name))

    original: Mapped[Transaction] = relationship(back_populates="category")
    selector: Mapped[CategorySelector] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return f"Category({self.name})"


catfk = Annotated[
    int,
    mapped_column(BigInteger, ForeignKey(TransactionCategory.id, ondelete="CASCADE")),
]


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[idfk] = mapped_column(primary_key=True)
    note: Mapped[str]

    original: Mapped[Transaction] = relationship(back_populates="note")


class Nordigen(Base):
    __tablename__ = "nordigen"

    name: Mapped[bankfk] = mapped_column(primary_key=True)
    bank_id: Mapped[Optional[str]]
    requisition_id: Mapped[Optional[str]]
    invert: Mapped[Optional[bool]]

    bank: Mapped[Bank] = relationship(back_populates="nordigen")

    def __repr__(self) -> str:
        return f"(bank_id={self.bank_id}, requisition_id={self.requisition_id}, invert={self.invert})"


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[idfk] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(primary_key=True)

    original: Mapped[Transaction] = relationship(back_populates="tags")


class CategoryRule(Base):
    __tablename__ = "categories_rules"

    name: Mapped[str] = mapped_column(
        ForeignKey(Category.name, ondelete="CASCADE"), primary_key=True
    )
    rule: Mapped[str] = mapped_column(primary_key=True)


class Selector(enum.Enum):
    unknown = enum.auto()
    nullifier = enum.auto()
    vacations = enum.auto()
    rules = enum.auto()
    algorithm = enum.auto()
    manual = enum.auto()


categoryselector = Annotated[
    Selector,
    mapped_column(Enum(Selector, inherit_schema=True), default=Selector.unknown),
]


class CategorySelector(Base):
    __tablename__ = "categories_selector"

    id: Mapped[catfk] = mapped_column(primary_key=True)
    selector: Mapped[categoryselector]

    category: Mapped[TransactionCategory] = relationship(back_populates="selector")
