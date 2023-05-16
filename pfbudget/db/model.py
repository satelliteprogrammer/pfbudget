from __future__ import annotations
from collections.abc import Mapping, MutableMapping, Sequence
from dataclasses import dataclass
import datetime as dt
import decimal
import enum
import re
from typing import Annotated, Any, Callable, Optional, Self, cast

from sqlalchemy import (
    BigInteger,
    Enum,
    ForeignKey,
    Integer,
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

    type_annotation_map = {
        enum.Enum: Enum(enum.Enum, create_constraint=True, inherit_schema=True),
    }


@dataclass
class Serializable:
    def serialize(self) -> Mapping[str, Any]:
        return dict(class_=type(self).__name__)

    @classmethod
    def deserialize(cls, map: Mapping[str, Any]) -> Self:
        raise NotImplementedError


class AccountType(enum.Enum):
    checking = enum.auto()
    savings = enum.auto()
    investment = enum.auto()
    mealcard = enum.auto()
    VISA = enum.auto()
    MASTERCARD = enum.auto()


class Bank(Base, Serializable):
    __tablename__ = "banks"

    name: Mapped[str] = mapped_column(primary_key=True)
    BIC: Mapped[str] = mapped_column(String(8))
    type: Mapped[AccountType]

    nordigen: Mapped[Optional[Nordigen]] = relationship(default=None, lazy="joined")

    def serialize(self) -> Mapping[str, Any]:
        nordigen = None
        if self.nordigen:
            nordigen = {
                "bank_id": self.nordigen.bank_id,
                "requisition_id": self.nordigen.requisition_id,
                "invert": self.nordigen.invert,
            }

        return super().serialize() | dict(
            name=self.name,
            BIC=self.BIC,
            type=self.type.name,
            nordigen=nordigen,
        )

    @classmethod
    def deserialize(cls, map: Mapping[str, Any]) -> Self:
        bank = cls(map["name"], map["BIC"], map["type"])
        if map["nordigen"]:
            bank.nordigen = Nordigen(**map["nordigen"])
        return bank


bankfk = Annotated[str, mapped_column(Text, ForeignKey(Bank.name))]

idpk = Annotated[
    int,
    mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    ),
]
money = Annotated[decimal.Decimal, mapped_column(Numeric(16, 2))]


class Transaction(Base, Serializable):
    __tablename__ = "transactions"

    id: Mapped[idpk] = mapped_column(init=False)
    date: Mapped[dt.date]
    description: Mapped[Optional[str]]
    amount: Mapped[money]

    split: Mapped[bool] = mapped_column(default=False)

    category: Mapped[Optional[TransactionCategory]] = relationship(
        back_populates="transaction", default=None, lazy="joined"
    )
    tags: Mapped[set[TransactionTag]] = relationship(default_factory=set, lazy="joined")
    note: Mapped[Optional[Note]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, default=None, lazy="joined"
    )

    type: Mapped[str] = mapped_column(init=False)
    __mapper_args__ = {"polymorphic_on": "type", "polymorphic_identity": "transaction"}

    def serialize(self) -> Mapping[str, Any]:
        category = None
        if self.category:
            category = {
                "name": self.category.name,
                "selector": self.category.selector.name,
            }

        return super().serialize() | dict(
            id=self.id,
            date=self.date.isoformat(),
            description=self.description,
            amount=str(self.amount),
            split=self.split,
            category=category if category else None,
            tags=[{"tag": tag.tag} for tag in self.tags],
            note={"note": self.note.note} if self.note else None,
            type=self.type,
        )

    @classmethod
    def deserialize(
        cls, map: Mapping[str, Any]
    ) -> Transaction | BankTransaction | MoneyTransaction | SplitTransaction:
        match map["type"]:
            case "bank":
                return BankTransaction.deserialize(map)
            case "money":
                return MoneyTransaction.deserialize(map)
            case "split":
                return SplitTransaction.deserialize(map)
            case _:
                return cls._deserialize(map)

    @classmethod
    def _deserialize(cls, map: Mapping[str, Any]) -> Self:
        category = None
        if map["category"]:
            category = TransactionCategory(map["category"]["name"])
            if map["category"]["selector"]:
                category.selector = map["category"]["selector"]

        tags: set[TransactionTag] = set()
        if map["tags"]:
            tags = set(TransactionTag(t["tag"]) for t in map["tags"])

        note = None
        if map["note"]:
            note = Note(map["note"]["note"])

        result = cls(
            dt.date.fromisoformat(map["date"]),
            map["description"],
            map["amount"],
            map["split"],
            category,
            tags,
            note,
        )

        if map["id"]:
            result.id = map["id"]
        return result

    def __lt__(self, other: Transaction):
        return self.date < other.date


idfk = Annotated[
    int, mapped_column(BigInteger, ForeignKey(Transaction.id, ondelete="CASCADE"))
]


class BankTransaction(Transaction):
    bank: Mapped[Optional[bankfk]] = mapped_column(default=None)

    __mapper_args__ = {"polymorphic_identity": "bank", "polymorphic_load": "inline"}

    def serialize(self) -> Mapping[str, Any]:
        map = cast(MutableMapping[str, Any], super().serialize())
        map["bank"] = self.bank
        return map

    @classmethod
    def deserialize(cls, map: Mapping[str, Any]) -> Self:
        transaction = cls._deserialize(map)
        transaction.bank = map["bank"]
        return transaction


class MoneyTransaction(Transaction):
    __mapper_args__ = {"polymorphic_identity": "money"}

    def serialize(self) -> Mapping[str, Any]:
        return super().serialize()

    @classmethod
    def deserialize(cls, map: Mapping[str, Any]) -> Self:
        return cls._deserialize(map)


class SplitTransaction(Transaction):
    original: Mapped[Optional[idfk]] = mapped_column(default=None)

    __mapper_args__ = {"polymorphic_identity": "split", "polymorphic_load": "inline"}

    def serialize(self) -> Mapping[str, Any]:
        map = cast(MutableMapping[str, Any], super().serialize())
        map["original"] = self.original
        return map

    @classmethod
    def deserialize(cls, map: Mapping[str, Any]) -> Self:
        transaction = cls._deserialize(map)
        transaction.original = map["original"]
        return transaction


class CategoryGroup(Base, Serializable):
    __tablename__ = "category_groups"

    name: Mapped[str] = mapped_column(primary_key=True)

    categories: Mapped[list[Category]] = relationship(
        default_factory=list, lazy="joined"
    )

    def serialize(self) -> Mapping[str, Any]:
        return super().serialize() | dict(name=self.name)

    @classmethod
    def deserialize(cls, map: Mapping[str, Any]) -> Self:
        return cls(map["name"])


class Category(Base, Serializable, repr=False):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(primary_key=True)
    group: Mapped[Optional[str]] = mapped_column(
        ForeignKey(CategoryGroup.name), default=None
    )

    rules: Mapped[list[CategoryRule]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        default_factory=list,
        lazy="joined",
    )
    schedule: Mapped[Optional[CategorySchedule]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True, default=None, lazy="joined"
    )

    def serialize(self) -> Mapping[str, Any]:
        rules: Sequence[Mapping[str, Any]] = []
        for rule in self.rules:
            rules.append(
                {
                    "start": rule.start.isoformat() if rule.start else None,
                    "end": rule.end.isoformat() if rule.end else None,
                    "description": rule.description,
                    "regex": rule.regex,
                    "bank": rule.bank,
                    "min": str(rule.min) if rule.min is not None else None,
                    "max": str(rule.max) if rule.max is not None else None,
                }
            )

        schedule = None
        if self.schedule:
            schedule = {
                "period": self.schedule.period.name if self.schedule.period else None,
                "period_multiplier": self.schedule.period_multiplier,
                "amount": self.schedule.amount,
            }

        return super().serialize() | dict(
            name=self.name,
            group=self.group,
            rules=rules,
            schedule=schedule,
        )

    @classmethod
    def deserialize(cls, map: Mapping[str, Any]) -> Self:
        rules: list[CategoryRule] = []
        for rule in map["rules"]:
            rules.append(
                CategoryRule(
                    dt.date.fromisoformat(rule["start"]) if rule["start"] else None,
                    dt.date.fromisoformat(rule["end"]) if rule["end"] else None,
                    rule["description"],
                    rule["regex"],
                    rule["bank"],
                    rule["min"],
                    rule["max"],
                )
            )

        return cls(
            map["name"],
            map["group"],
            rules,
            CategorySchedule(**map["schedule"]) if map["schedule"] else None,
        )

    def __repr__(self) -> str:
        return (
            f"Category(name={self.name}, group={self.group}, #rules={len(self.rules)},"
            f" schedule={self.schedule})"
        )


catfk = Annotated[
    str,
    mapped_column(ForeignKey(Category.name, ondelete="CASCADE")),
]


class CategorySelector(enum.Enum):
    unknown = enum.auto()
    nullifier = enum.auto()
    vacations = enum.auto()
    rules = enum.auto()
    algorithm = enum.auto()
    manual = enum.auto()


class TransactionCategory(Base):
    __tablename__ = "transactions_categorized"

    id: Mapped[idfk] = mapped_column(primary_key=True, init=False)
    name: Mapped[catfk]

    selector: Mapped[CategorySelector] = mapped_column(default=CategorySelector.unknown)

    transaction: Mapped[Transaction] = relationship(
        back_populates="category", init=False, compare=False
    )


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[idfk] = mapped_column(primary_key=True, init=False)
    note: Mapped[str]


class Nordigen(Base):
    __tablename__ = "banks_nordigen"

    name: Mapped[bankfk] = mapped_column(primary_key=True, init=False)
    bank_id: Mapped[Optional[str]]
    requisition_id: Mapped[Optional[str]]
    invert: Mapped[Optional[bool]] = mapped_column(default=None)


class Tag(Base, Serializable):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(primary_key=True)

    rules: Mapped[list[TagRule]] = relationship(
        cascade="all, delete-orphan",
        passive_deletes=True,
        default_factory=list,
        lazy="joined",
    )

    def serialize(self) -> Mapping[str, Any]:
        rules: Sequence[Mapping[str, Any]] = []
        for rule in self.rules:
            rules.append(
                {
                    "start": rule.start,
                    "end": rule.end,
                    "description": rule.description,
                    "regex": rule.regex,
                    "bank": rule.bank,
                    "min": str(rule.min) if rule.min is not None else None,
                    "max": str(rule.max) if rule.max is not None else None,
                }
            )

        return super().serialize() | dict(name=self.name, rules=rules)

    @classmethod
    def deserialize(cls, map: Mapping[str, Any]) -> Self:
        rules: list[TagRule] = []
        for rule in map["rules"]:
            rules.append(
                TagRule(
                    dt.date.fromisoformat(rule["start"]) if rule["start"] else None,
                    dt.date.fromisoformat(rule["end"]) if rule["end"] else None,
                    rule["description"],
                    rule["regex"],
                    rule["bank"],
                    rule["min"],
                    rule["max"],
                )
            )

        return cls(map["name"], rules)


class TransactionTag(Base, unsafe_hash=True):
    __tablename__ = "transactions_tagged"

    id: Mapped[idfk] = mapped_column(primary_key=True, init=False)
    tag: Mapped[str] = mapped_column(ForeignKey(Tag.name), primary_key=True)


class SchedulePeriod(enum.Enum):
    daily = enum.auto()
    weekly = enum.auto()
    monthly = enum.auto()
    yearly = enum.auto()


class CategorySchedule(Base):
    __tablename__ = "category_schedules"

    name: Mapped[catfk] = mapped_column(primary_key=True, init=False)
    period: Mapped[Optional[SchedulePeriod]]
    period_multiplier: Mapped[Optional[int]]
    amount: Mapped[Optional[int]]


class Link(Base):
    __tablename__ = "links"

    original: Mapped[idfk] = mapped_column(primary_key=True)
    link: Mapped[idfk] = mapped_column(primary_key=True)


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[idpk] = mapped_column(init=False)
    start: Mapped[Optional[dt.date]] = mapped_column(default=None)
    end: Mapped[Optional[dt.date]] = mapped_column(default=None)
    description: Mapped[Optional[str]] = mapped_column(default=None)
    regex: Mapped[Optional[str]] = mapped_column(default=None)
    bank: Mapped[Optional[str]] = mapped_column(default=None)
    min: Mapped[Optional[money]] = mapped_column(default=None)
    max: Mapped[Optional[money]] = mapped_column(default=None)

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

    @staticmethod
    def exists(r: Optional[Any], op: Callable[[Any], bool]) -> bool:
        return op(r) if r is not None else True


class CategoryRule(Rule):
    __tablename__ = "category_rules"

    id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(Rule.id, ondelete="CASCADE"),
        primary_key=True,
        init=False,
    )
    name: Mapped[catfk] = mapped_column(init=False)

    __mapper_args__ = {
        "polymorphic_identity": "category_rule",
    }


class TagRule(Rule):
    __tablename__ = "tag_rules"

    id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(Rule.id, ondelete="CASCADE"),
        primary_key=True,
        init=False,
    )
    tag: Mapped[str] = mapped_column(
        ForeignKey(Tag.name, ondelete="CASCADE"), init=False
    )

    __mapper_args__ = {
        "polymorphic_identity": "tag_rule",
    }
