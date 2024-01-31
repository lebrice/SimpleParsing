"""Simple, Elegant Argument parsing.

@author: Fabrice Normandin
"""
from . import helpers, utils, wrappers
from .conflicts import ConflictResolution
from .decorators import main
from .help_formatter import SimpleHelpFormatter
from .helpers import (
    Partial,
    Serializable,
    choice,
    config_for,
    field,
    flag,
    list_field,
    mutable_field,
    subgroups,
    subparsers,
)
from .parsing import (
    ArgumentGenerationMode,
    ArgumentParser,
    DashVariant,
    NestedMode,
    ParsingError,
    parse,
    parse_known_args,
)
from .replace import replace, replace_subgroups
from .utils import InconsistentArgumentError

__all__ = [
    "ArgumentGenerationMode",
    "ArgumentParser",
    "choice",
    "config_for",
    "ConflictResolution",
    "DashVariant",
    "field",
    "flag",
    "helpers",
    "InconsistentArgumentError",
    "list_field",
    "main",
    "mutable_field",
    "NestedMode",
    "parse_known_args",
    "parse",
    "ParsingError",
    "Partial",
    "replace",
    "replace_subgroups",
    "Serializable",
    "SimpleHelpFormatter",
    "subgroups",
    "subparsers",
    "utils",
    "wrappers",
]
