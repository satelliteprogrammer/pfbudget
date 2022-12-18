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
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    MappedAsDataclass,
    relationship,
)

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

idpk = Annotated[
    int, mapped_column(BigInteger, primary_key=True, autoincrement=True, init=False)
]
money = Annotated[Decimal, mapped_column(Numeric(16, 2))]


class Transaction(Base):
    __tablename__ = "originals"

    id: Mapped[idpk]
    date: Mapped[dt.date]
    description: Mapped[Optional[str]]
    bank: Mapped[bankfk]
    amount: Mapped[money]

    category: Mapped[Optional[TransactionCategory]] = relationship()
    note: Mapped[Optional[Note]] = relationship(back_populates="original", default=None)
    tags: Mapped[Optional[set[TransactionTag]]] = relationship(
        back_populates="original",
        cascade="all, delete-orphan",
        passive_deletes=True,
        default=None,
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
    group: Mapped[Optional[str]] = mapped_column(
        ForeignKey(CategoryGroup.name), default=None
    )

    rules: Mapped[Optional[set[CategoryRule]]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, default_factory=set
    )
    schedule: Mapped[CategorySchedule] = relationship(
        back_populates="category", default=None
    )

    def __repr__(self) -> str:
        return f"Category(name={self.name}, group={self.group}, #rules={len(self.rules)}, schedule={self.schedule})"


catfk = Annotated[
    str,
    mapped_column(ForeignKey(Category.name, ondelete="CASCADE")),
]


class TransactionCategory(Base):
    __tablename__ = "categorized"

    id: Mapped[idfk] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(ForeignKey(Category.name))

    selector: Mapped[CategorySelector] = relationship()

    def __repr__(self) -> str:
        return f"Category({self.name})"


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
    __tablename__ = "tags_available"

    name: Mapped[str] = mapped_column(primary_key=True)

    rules: Mapped[Optional[set[TagRule]]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, default_factory=set
    )


class TransactionTag(Base):
    __tablename__ = "tags"

    id: Mapped[idfk] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(ForeignKey(Tag.name), primary_key=True)

    original: Mapped[Transaction] = relationship(back_populates="tags")


class CategoryRule(Base):
    __tablename__ = "categories_rules"

    id: Mapped[idpk]
    name: Mapped[catfk]
    date: Mapped[Optional[dt.date]]
    description: Mapped[Optional[str]]
    regex: Mapped[Optional[str]]
    bank: Mapped[Optional[str]]
    min: Mapped[Optional[money]]
    max: Mapped[Optional[money]]

    def __hash__(self):
        return hash(self.id)


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

    id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(TransactionCategory.id, ondelete="CASCADE"),
        primary_key=True,
        init=False,
    )
    selector: Mapped[categoryselector]


class Period(enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


scheduleperiod = Annotated[Selector, mapped_column(Enum(Period, inherit_schema=True))]


class CategorySchedule(Base):
    __tablename__ = "categories_schedules"

    name: Mapped[catfk] = mapped_column(primary_key=True)
    period: Mapped[Optional[scheduleperiod]]
    period_multiplier: Mapped[Optional[int]]
    amount: Mapped[Optional[int]]

    category: Mapped[Category] = relationship(back_populates="schedule")

    def __repr__(self) -> str:
        return f"{self.name} schedule=Schedule(period={self.period}, multiplier={self.period_multiplier}, amount={self.amount})"


class TagRule(Base):
    __tablename__ = "tag_rules"

    id: Mapped[idpk]
    tag: Mapped[str] = mapped_column(ForeignKey(Tag.name, ondelete="CASCADE"))
    date: Mapped[Optional[dt.date]]
    description: Mapped[Optional[str]]
    regex: Mapped[Optional[str]]
    bank: Mapped[Optional[str]]
    min: Mapped[Optional[money]]
    max: Mapped[Optional[money]]
