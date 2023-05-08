from collections.abc import Mapping
from dataclasses import fields
from functools import singledispatch
from typing import Any

from pfbudget.db.model import Transaction, TransactionCategory, TransactionTag, Note


class NotSerializableError(Exception):
    pass


@singledispatch
def serialize(obj: Any) -> Mapping[str, Any]:
    return {field.name: getattr(obj, field.name) for field in fields(obj)}


@serialize.register
def _(obj: Transaction) -> Mapping[str, Any]:
    category = None
    if obj.category:
        category = {
            "name": obj.category.name,
            "selector": str(obj.category.selector)
            if obj.category.selector
            else None,
        }

    return dict(
        id=obj.id,
        date=obj.date.isoformat(),
        description=obj.description,
        amount=str(obj.amount),
        split=obj.split,
        category=category if category else None,
        tags=[{"tag": tag.tag} for tag in obj.tags],
        note=obj.note,
        type=obj.type,
    )


@serialize.register
def _(_: TransactionCategory) -> Mapping[str, Any]:
    raise NotSerializableError("TransactionCategory")


@serialize.register
def _(_: TransactionTag) -> Mapping[str, Any]:
    raise NotSerializableError("TransactionTag")


@serialize.register
def _(_: Note) -> Mapping[str, Any]:
    raise NotSerializableError("Note")
