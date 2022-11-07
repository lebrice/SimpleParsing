"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
from . import helpers, utils, wrappers
from .conflicts import ConflictResolution
from .decorators import main
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
    "ArgumentGenerationMode",
    "ArgumentParser",
    "choice",
    "ConflictResolution",
    "DashVariant",
    "field",
    "flag",
    "helpers",
    "InconsistentArgumentError",
    "list_field",
    "main",
    "mutable_field",
    "MutableField",
    "NestedMode",
    "parse_known_args",
    "parse",
    "ParsingError",
    "Serializable",
    "SimpleHelpFormatter",
    "subgroups",
    "subparsers",
    "utils",
    "wrappers",
]

from . import _version

__version__ = _version.get_versions()["version"]
