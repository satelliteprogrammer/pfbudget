from abc import ABC, abstractmethod
import json
from pathlib import Path
import pickle
from typing import Type

from pfbudget.common.types import ExportFormat
from pfbudget.db.client import Client
from pfbudget.db.model import (
    Bank,
    Category,
    CategoryGroup,
    Serializable,
    Tag,
    Transaction,
)

# required for the backup import
import pfbudget.db.model


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        raise NotImplementedError

    def undo(self) -> None:
        raise NotImplementedError


class ExportCommand(Command):
    def __init__(
        self, client: Client, what: Type[Serializable], fn: Path, format: ExportFormat
    ):
        self.__client = client
        self.what = what
        self.fn = fn
        self.format = format

    def execute(self) -> None:
        values = self.__client.select(self.what)
        match self.format:
            case ExportFormat.JSON:
                with open(self.fn, "w", newline="") as f:
                    json.dump([e.serialize() for e in values], f, indent=4)
            case ExportFormat.pickle:
                raise AttributeError("pickle export not working at the moment!")
                with open(self.fn, "wb") as f:
                    pickle.dump(values, f)


class ImportCommand(Command):
    def __init__(
        self, client: Client, what: Type[Serializable], fn: Path, format: ExportFormat
    ):
        self.__client = client
        self.what = what
        self.fn = fn
        self.format = format

    def execute(self) -> None:
        match self.format:
            case ExportFormat.JSON:
                with open(self.fn, "r") as f:
                    try:
                        values = json.load(f)
                        values = [self.what.deserialize(v) for v in values]
                    except json.JSONDecodeError as e:
                        raise ImportFailedError(e)

            case ExportFormat.pickle:
                raise AttributeError("pickle import not working at the moment!")
                with open(self.fn, "rb") as f:
                    values = pickle.load(f)

        self.__client.insert(values)


class ImportFailedError(Exception):
    pass


class BackupCommand(Command):
    def __init__(self, client: Client, fn: Path, format: ExportFormat) -> None:
        self.__client = client
        self.fn = fn
        self.format = format

    def execute(self) -> None:
        banks = self.__client.select(Bank)
        groups = self.__client.select(CategoryGroup)
        categories = self.__client.select(Category)
        tags = self.__client.select(Tag)
        transactions = self.__client.select(Transaction)

        values = [*banks, *groups, *categories, *tags, *transactions]

        match self.format:
            case ExportFormat.JSON:
                with open(self.fn, "w", newline="") as f:
                    json.dump([e.serialize() for e in values], f, indent=4)
            case ExportFormat.pickle:
                raise AttributeError("pickle export not working at the moment!")


class ImportBackupCommand(Command):
    def __init__(self, client: Client, fn: Path, format: ExportFormat) -> None:
        self.__client = client
        self.fn = fn
        self.format = format

    def execute(self) -> None:
        match self.format:
            case ExportFormat.JSON:
                with open(self.fn, "r") as f:
                    try:
                        values = json.load(f)
                        values = [
                            getattr(pfbudget.db.model, v["class_"]).deserialize(v)
                            for v in values
                        ]
                    except json.JSONDecodeError as e:
                        raise ImportFailedError(e)

            case ExportFormat.pickle:
                raise AttributeError("pickle import not working at the moment!")

        self.__client.insert(values)
