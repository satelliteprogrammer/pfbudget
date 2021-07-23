__all__ = ["run", "parse_data", "categorize_data"]
__author__ = "Luís Murta"
__version__ = "0.1"

from .categories import categorize_data
from .parsers import parse_data
from .runnable import run
