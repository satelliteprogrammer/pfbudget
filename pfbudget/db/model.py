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
    metadata = MetaData(
        schema="pfbudget",
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
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


class Bank(Base, Export):
    __tablename__ = "banks"

    name: Mapped[str] = mapped_column(unique=True)
    BIC: Mapped[str] = mapped_column(String(8), primary_key=True)
    type: Mapped[accounttype] = mapped_column(primary_key=True)

    nordigen: Mapped[Optional[Nordigen]] = relationship(lazy="joined", init=False)

    @property
    def format(self) -> dict[str, Any]:
        return dict(
            name=self.name,
            BIC=self.BIC,
            type=self.type,
            nordigen=self.nordigen.format if self.nordigen else None,
        )


bankfk = Annotated[str, mapped_column(Text, ForeignKey(Bank.name))]

idpk = Annotated[int, mapped_column(BigInteger, primary_key=True, autoincrement=True)]
money = Annotated[decimal.Decimal, mapped_column(Numeric(16, 2))]


class Transaction(Base, Export):
    __tablename__ = "transactions"

    id: Mapped[idpk] = mapped_column(init=False)
    date: Mapped[dt.date]
    description: Mapped[Optional[str]]
    amount: Mapped[money]

    split: Mapped[bool] = mapped_column(init=False, default=False)

    type: Mapped[str] = mapped_column(init=False)

    category: Mapped[Optional[TransactionCategory]] = relationship(init=False)
    note: Mapped[Optional[Note]] = relationship(
        cascade="all, delete-orphan", init=False, passive_deletes=True
    )
    tags: Mapped[set[TransactionTag]] = relationship(init=False)

    __mapper_args__ = {"polymorphic_on": "type", "polymorphic_identity": "transaction"}

    @property
    def format(self) -> dict[str, Any]:
        return dict(
            id=self.id,
            date=self.date,
            description=self.description,
            amount=self.amount,
            split=self.split,
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

    __mapper_args__ = {"polymorphic_identity": "bank", "polymorphic_load": "inline"}

    @property
    def format(self) -> dict[str, Any]:
        return super().format | dict(bank=self.bank)


class MoneyTransaction(Transaction):
    __mapper_args__ = {"polymorphic_identity": "money"}


class SplitTransaction(Transaction):
    original: Mapped[idfk] = mapped_column(nullable=True)

    __mapper_args__ = {"polymorphic_identity": "split", "polymorphic_load": "inline"}

    @property
    def format(self) -> dict[str, Any]:
        return super().format | dict(original=self.original)


class CategoryGroup(Base, Export):
    __tablename__ = "category_groups"

    name: Mapped[str] = mapped_column(primary_key=True)

    @property
    def format(self) -> dict[str, Any]:
        return dict(name=self.name)


class Category(Base, Export):
    __tablename__ = "categories"

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
        return (
            f"Category(name={self.name}, group={self.group}, #rules={len(self.rules)},"
            f" schedule={self.schedule})"
        )

    @property
    def format(self) -> dict[str, Any]:
        return dict(
            name=self.name,
            group=self.group if self.group else None,
            rules=[rule.format for rule in self.rules],
            schedule=self.schedule.format if self.schedule else None,
        )


catfk = Annotated[
    str,
    mapped_column(ForeignKey(Category.name, ondelete="CASCADE")),
]


class TransactionCategory(Base, Export):
    __tablename__ = "transactions_categorized"

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


class Nordigen(Base, Export):
    __tablename__ = "banks_nordigen"

    name: Mapped[bankfk] = mapped_column(primary_key=True)
    bank_id: Mapped[Optional[str]]
    requisition_id: Mapped[Optional[str]]
    invert: Mapped[Optional[bool]]

    @property
    def format(self) -> dict[str, Any]:
        return dict(
            name=self.name,
            bank_id=self.bank_id,
            requisition_id=self.requisition_id,
            invert=self.invert,
        )


class Tag(Base):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(primary_key=True)

    rules: Mapped[set[TagRule]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, default_factory=set
    )


class TransactionTag(Base, Export):
    __tablename__ = "transactions_tagged"

    id: Mapped[idfk] = mapped_column(primary_key=True, init=False)
    tag: Mapped[str] = mapped_column(ForeignKey(Tag.name), primary_key=True)

    @property
    def format(self):
        return dict(tag=self.tag)

    def __hash__(self):
        return hash(self.id)


class Selector_T(enum.Enum):
    unknown = enum.auto()
    nullifier = enum.auto()
    vacations = enum.auto()
    rules = enum.auto()
    algorithm = enum.auto()
    manual = enum.auto()


categoryselector = Annotated[
    Selector_T,
    mapped_column(Enum(Selector_T, inherit_schema=True), default=Selector_T.unknown),
]


class CategorySelector(Base, Export):
    __tablename__ = "category_selectors"

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


scheduleperiod = Annotated[Selector_T, mapped_column(Enum(Period, inherit_schema=True))]


class CategorySchedule(Base, Export):
    __tablename__ = "category_schedules"

    name: Mapped[catfk] = mapped_column(primary_key=True)
    period: Mapped[Optional[scheduleperiod]]
    period_multiplier: Mapped[Optional[int]]
    amount: Mapped[Optional[int]]

    @property
    def format(self) -> dict[str, Any]:
        return dict(
            name=self.name,
            period=self.period,
            period_multiplier=self.period_multiplier,
            amount=self.amount,
        )


class Link(Base):
    __tablename__ = "links"

    original: Mapped[idfk] = mapped_column(primary_key=True)
    link: Mapped[idfk] = mapped_column(primary_key=True)


class Rule(Base, Export):
    __tablename__ = "rules"

    id: Mapped[idpk] = mapped_column(init=False)
    start: Mapped[Optional[dt.date]]
    end: Mapped[Optional[dt.date]]
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

    def matches(self, t: BankTransaction) -> bool:
        valid = None
        if self.regex:
            valid = re.compile(self.regex, re.IGNORECASE)

        ops = (
            Rule.exists(self.start, lambda r: r < t.date),
            Rule.exists(self.end, lambda r: r > t.date),
            Rule.exists(self.description, lambda r: r == t.description),
            Rule.exists(
                valid,
                lambda r: r.search(t.description) if t.description else False,
            ),
            Rule.exists(self.bank, lambda r: r == t.bank),
            Rule.exists(self.min, lambda r: r < t.amount),
            Rule.exists(self.max, lambda r: r > t.amount),
        )

        if all(ops):
            return True

        return False

    @property
    def format(self) -> dict[str, Any]:
        return dict(
            start=self.start,
            end=self.end,
            description=self.description,
            regex=self.regex,
            bank=self.bank,
            min=self.min,
            max=self.max,
            type=self.type,
        )

    @staticmethod
    def exists(r, op) -> bool:
        return op(r) if r is not None else True


class CategoryRule(Rule):
    __tablename__ = "category_rules"

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
