from abc import ABC, abstractmethod
import json
from pathlib import Path
import pickle
from typing import Any, Type

from pfbudget.common.types import ExportFormat
from pfbudget.db.client import Client
from pfbudget.utils.serializer import serialize


class Command(ABC):
    @abstractmethod
    def execute(self) -> None:
        raise NotImplementedError

    def undo(self) -> None:
        raise NotImplementedError


class ExportCommand(Command):
    def __init__(self, client: Client, what: Type[Any], fn: Path, format: ExportFormat):
        self.__client = client
        self.what = what
        self.fn = fn
        self.format = format

    def execute(self) -> None:
        values = self.__client.select(self.what)
        match self.format:
            case ExportFormat.JSON:
                with open(self.fn, "w", newline="") as f:
                    json.dump([serialize(e) for e in values], f, indent=4, default=str)
            case ExportFormat.pickle:
                with open(self.fn, "wb") as f:
                    pickle.dump([serialize(e) for e in values], f)
