from collections.abc import Mapping
from dataclasses import fields
from functools import singledispatch
from typing import Any

from pfbudget.db.model import Transaction, TransactionCategory


@singledispatch
def serialize(obj: Any) -> Mapping[str, Any]:
    raise NotImplementedError


@serialize.register
def _(obj: Transaction) -> Mapping[str, Any]:
    return dict((field.name, getattr(obj, field.name)) for field in fields(obj))


@serialize.register
def _(obj: TransactionCategory) -> Mapping[str, Any]:
    return dict((field.name, getattr(obj, field.name)) for field in fields(obj))
