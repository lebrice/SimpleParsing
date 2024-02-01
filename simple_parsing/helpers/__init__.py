"""Collection of helper classes and functions to reduce boilerplate code."""
from .fields import (
    choice,
    dict_field,
    field,
    flag,
    flags,
    list_field,
    mutable_field,
    set_field,
    subparsers,
)
from .flatten import FlattenedAccess
from .hparams import HyperParameters
from .partial import Partial, config_for
from .serialization import FrozenSerializable, Serializable, SimpleJsonEncoder, encode
from .subgroups import subgroups

try:
    from .serialization import YamlSerializable
except ImportError:
    pass

# For backward compatibility purposes
JsonSerializable = Serializable
SimpleEncoder = SimpleJsonEncoder

__all__ = [
    "FlattenedAccess",
    "HyperParameters",
    "Partial",
    "config_for",
    "FrozenSerializable",
    "Serializable",
    "SimpleJsonEncoder",
    "encode",
    "JsonSerializable",
    "SimpleEncoder",
    "YamlSerializable",
    "field",
    "choice",
    "list_field",
    "dict_field",
    "set_field",
    "mutable_field",
    "subparsers",
    "flag",
    "flags",
    "subgroups",
]
