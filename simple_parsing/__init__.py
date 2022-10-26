"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
from . import helpers, utils, wrappers
from .conflicts import ConflictResolution
from .help_formatter import SimpleHelpFormatter
from .helpers import (
    MutableField,
    Serializable,
    choice,
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
from .utils import InconsistentArgumentError

__all__ = [
    "helpers",
    "utils",
    "wrappers",
    "ConflictResolution",
    "SimpleHelpFormatter",
    "MutableField",
    "Serializable",
    "choice",
    "field",
    "flag",
    "list_field",
    "mutable_field",
    "subgroups",
    "subparsers",
    "ArgumentParser",
    "DashVariant",
    "ParsingError",
    "parse",
    "parse_known_args",
    "ArgumentGenerationMode",
    "NestedMode",
    "InconsistentArgumentError",
]

from . import _version

__version__ = _version.get_versions()["version"]
