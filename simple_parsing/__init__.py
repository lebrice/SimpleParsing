"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
from . import helpers, utils, wrappers
from .conflicts import ConflictResolution
from .helpers import (MutableField, Serializable, SimpleHelpFormatter, choice,
                      field, flag, list_field, mutable_field, subparsers)
from .parsing import ArgumentParser, ParsingError
from .utils import InconsistentArgumentError

__all__ = [
    "helpers", "utils", "wrappers",
    "ConflictResolution",
    "MutableField", "Serializable", "SimpleHelpFormatter", "choice",
    "field", "flag", "list_field", "mutable_field", "subparsers",
    "ArgumentParser",
    "InconsistentArgumentError",
]
