from __future__ import annotations
import datetime as dt
import decimal
import enum
import re
from typing import Annotated, Any, Optional

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


class Export:
    @property
    def format(self) -> dict[str, Any]:
        raise NotImplementedError


class Bank(Base):
    __tablename__ = "banks"

    name: Mapped[str] = mapped_column(unique=True)
    BIC: Mapped[str] = mapped_column(String(8), primary_key=True)
    type: Mapped[accounttype] = mapped_column(primary_key=True)

    nordigen: Mapped[Optional[Nordigen]] = relationship(lazy="joined", init=False)


bankfk = Annotated[str, mapped_column(Text, ForeignKey(Bank.name))]

idpk = Annotated[int, mapped_column(BigInteger, primary_key=True, autoincrement=True)]
money = Annotated[decimal.Decimal, mapped_column(Numeric(16, 2))]


class Transaction(Base, Export):
    __tablename__ = "originals"

    id: Mapped[idpk] = mapped_column(init=False)
    date: Mapped[dt.date]
    description: Mapped[Optional[str]]
    amount: Mapped[money]

    type: Mapped[str] = mapped_column(init=False)

    category: Mapped[Optional[TransactionCategory]] = relationship(init=False)
    note: Mapped[Optional[Note]] = relationship(init=False)
    tags: Mapped[set[TransactionTag]] = relationship(init=False)

    __mapper_args__ = {"polymorphic_on": "type", "polymorphic_identity": "transaction"}

    @property
    def format(self) -> dict[str, Any]:
        return dict(
            date=self.date,
            description=self.description,
            amount=self.amount,
            type=self.type,
            category=self.category.format if self.category else None,
            # TODO note
            tags=[tag.format for tag in self.tags] if self.tags else None,
        )

    def __lt__(self, other: Transaction):
        return self.date < other.date


idfk = Annotated[
    int, mapped_column(BigInteger, ForeignKey(Transaction.id, ondelete="CASCADE"))
]


class BankTransaction(Transaction):
    bank: Mapped[bankfk] = mapped_column(nullable=True)
    split: Mapped[bool] = mapped_column(use_existing_column=True, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "bank", "polymorphic_load": "inline"}

    @property
    def format(self) -> dict[str, Any]:
        return super().format | dict(bank=self.bank)


class MoneyTransaction(Transaction):
    split: Mapped[bool] = mapped_column(use_existing_column=True, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "money"}


class SplitTransaction(Transaction):
    original: Mapped[idfk] = mapped_column(nullable=True)

    __mapper_args__ = {"polymorphic_identity": "split", "polymorphic_load": "inline"}

    @property
    def format(self) -> dict[str, Any]:
        return super().format | dict(original=self.original)


class CategoryGroup(Base):
    __tablename__ = "categories_groups"

    name: Mapped[str] = mapped_column(primary_key=True)


class Category(Base):
    __tablename__ = "categories_available"

    name: Mapped[str] = mapped_column(primary_key=True)
    group: Mapped[Optional[str]] = mapped_column(
        ForeignKey(CategoryGroup.name), default=None
    )

    rules: Mapped[set[CategoryRule]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, default_factory=set
    )
    schedule: Mapped[Optional[CategorySchedule]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, default=None
    )

    def __repr__(self) -> str:
        return f"Category(name={self.name}, group={self.group}, #rules={len(self.rules)}, schedule={self.schedule})"


catfk = Annotated[
    str,
    mapped_column(ForeignKey(Category.name, ondelete="CASCADE")),
]


class TransactionCategory(Base, Export):
    __tablename__ = "categorized"

    id: Mapped[idfk] = mapped_column(primary_key=True, init=False)
    name: Mapped[catfk]

    selector: Mapped[CategorySelector] = relationship(
        cascade="all, delete-orphan", lazy="joined"
    )

    @property
    def format(self):
        return dict(name=self.name, selector=self.selector.format)


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[idfk] = mapped_column(primary_key=True, init=False)
    note: Mapped[str]


class Nordigen(Base):
    __tablename__ = "nordigen"

    name: Mapped[bankfk] = mapped_column(primary_key=True)
    bank_id: Mapped[Optional[str]]
    requisition_id: Mapped[Optional[str]]
    invert: Mapped[Optional[bool]]


class Tag(Base):
    __tablename__ = "tags_available"

    name: Mapped[str] = mapped_column(primary_key=True)

    rules: Mapped[set[TagRule]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, default_factory=set
    )


class TransactionTag(Base, Export):
    __tablename__ = "tags"

    id: Mapped[idfk] = mapped_column(primary_key=True, init=False)
    tag: Mapped[str] = mapped_column(ForeignKey(Tag.name), primary_key=True)

    @property
    def format(self):
        return dict(tag=self.tag)

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


class CategorySelector(Base, Export):
    __tablename__ = "categories_selector"

    id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(TransactionCategory.id, ondelete="CASCADE"),
        primary_key=True,
        init=False,
    )
    selector: Mapped[categoryselector]

    @property
    def format(self):
        return dict(selector=self.selector)


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


class Link(Base):
    __tablename__ = "links"

    original: Mapped[idfk] = mapped_column(primary_key=True)
    link: Mapped[idfk] = mapped_column(primary_key=True)


class Rule(Base, Export):
    __tablename__ = "rules"

    id: Mapped[idpk] = mapped_column(init=False)
    date: Mapped[Optional[dt.date]]
    description: Mapped[Optional[str]]
    regex: Mapped[Optional[str]]
    bank: Mapped[Optional[str]]
    min: Mapped[Optional[money]]
    max: Mapped[Optional[money]]

    type: Mapped[str] = mapped_column(init=False)

    __mapper_args__ = {
        "polymorphic_identity": "rule",
        "polymorphic_on": "type",
    }

    def matches(self, transaction: BankTransaction) -> bool:
        if (
            (self.date and self.date < transaction.date)
            or (
                self.description
                and transaction.description
                and self.description not in transaction.description
            )
            or (
                self.regex
                and transaction.description
                and not re.compile(self.regex, re.IGNORECASE).search(
                    transaction.description
                )
            )
            or (self.bank and self.bank != transaction.bank)
            or (self.min and self.min > transaction.amount)
            or (self.max and self.max < transaction.amount)
        ):
            return False
        return True

    @property
    def format(self) -> dict[str, Any]:
        return dict(
            date=self.date,
            description=self.description,
            regex=self.regex,
            bank=self.bank,
            min=self.min,
            max=self.max,
            type=self.type,
        )


class CategoryRule(Rule):
    __tablename__ = "categories_rules"

    id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(Rule.id, ondelete="CASCADE"),
        primary_key=True,
        init=False,
    )
    name: Mapped[catfk]

    __mapper_args__ = {
        "polymorphic_identity": "category_rule",
    }

    @property
    def format(self) -> dict[str, Any]:
        return super().format | dict(name=self.name)

    def __hash__(self):
        return hash(self.id)


class TagRule(Rule):
    __tablename__ = "tag_rules"

    id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(Rule.id, ondelete="CASCADE"),
        primary_key=True,
        init=False,
    )
    tag: Mapped[str] = mapped_column(ForeignKey(Tag.name, ondelete="CASCADE"))

    __mapper_args__ = {
        "polymorphic_identity": "tag_rule",
    }

    @property
    def format(self) -> dict[str, Any]:
        return super().format | dict(tag=self.tag)

    def __hash__(self):
        return hash(self.id)
