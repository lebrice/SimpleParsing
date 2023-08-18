from __future__ import annotations

import argparse
import dataclasses
from argparse import (
    Action,
)
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import (
    Any,
    Generic,
    Literal,
    Sequence,
    TypeGuard,
    TypeVar,
    TypedDict,
    Protocol,
    ClassVar,
    TYPE_CHECKING,
)
import enum
from typing_extensions import Required

if TYPE_CHECKING:
    from refactored_parsing.parsing import ArgumentParser


T = TypeVar("T")


class Dataclass(Protocol):
    __dataclass_fields__: ClassVar[dict[str, dataclasses.Field]]


def is_dataclass(cls: type) -> TypeGuard[Dataclass]:
    return dataclasses.is_dataclass(cls)


DataclassT = TypeVar("DataclassT", bound=Dataclass)


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class ArgparseParserState:
    actions: list[Action]
    option_string_actions: dict[str, Action]

    registries: dict[str, dict[Literal["action", "type"] | None, type[argparse.Action]]]

    # action storage
    actions: list[argparse.Action]
    option_string_actions: dict[str, argparse.Action]

    # groups
    action_groups: list[argparse._ArgumentGroup]
    mutually_exclusive_groups: list[argparse._MutuallyExclusiveGroup]

    # defaults storage
    defaults: dict[str, Any]

    has_negative_number_optionals: list[bool]


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class AddedDcArguments(Generic[DataclassT]):
    dataclass: type[DataclassT]
    dest: str
    prefix: str = ""
    default: DataclassT | None = None


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class ParserState(ArgparseParserState):
    """The state of the ArgumentParser (everything useful that is saved on `self`)."""

    added_dc_args: Sequence[AddedDcArguments]

    conflict_resolution: ConflictResolution
    dashes_or_underscores: DashesOrUnderscores
    nested_field_display: NestedFieldDisplay
    config_path: Path | str | Sequence[Path | str] | None
    remove_root_from_option_strings: bool


class AddArgumentGroupKwargs(TypedDict, total=False):
    title: str | None
    description: str | None
    prefix_chars: str
    argument_default: Any
    conflict_handler: str


class AddArgumentKwargs(TypedDict, Generic[T], total=False):
    option_strings: Sequence[str]
    action: str | type[argparse.Action]
    nargs: int | argparse._NArgsStr | argparse._SUPPRESS_T
    const: Any
    default: T
    type: Callable[[str], T] | argparse.FileType
    choices: Iterable[T] | None
    required: bool
    help: str | None
    metavar: str | tuple[str, ...] | None
    dest: str
    version: str


class GeneratedAddArgumentKwargs(TypedDict, Generic[T], total=False):
    option_strings: Required[Sequence[str]]
    dest: Required[str]
    action: str | type[argparse.Action]
    nargs: int | argparse._NArgsStr | argparse._SUPPRESS_T
    const: Any
    default: T
    type: Callable[[str], T] | argparse.FileType
    choices: Iterable[T] | None
    required: bool
    help: str | None
    metavar: str | tuple[str, ...] | None
    version: str


class FieldMetaData(TypedDict, Generic[T]):
    alias: list[str]
    to_dict: bool
    cmd: bool
    positional: bool
    encoding_fn: Callable[[T], Any] | None
    decoding_fn: Callable[[Any], T] | None
    add_argument_overrides: AddArgumentKwargs[T]


class ConflictResolution(enum.Enum):
    """Determines how to generate prefixes when adding the same dataclass more than once."""

    AUTO = enum.auto()
    """The shortest prefix that can differentiate between all the conflicting arguments is used."""

    NONE = enum.auto()
    """Disallow using the same dataclass in two different destinations without explicit prefixes.

    A prefix needs to be passed to `ArgumentParser.add_arguments` for each dataclass.
    """

    EXPLICIT = enum.auto()
    """When the same dataclass is used twice, use their full destination as the option strings."""

    ALWAYS_MERGE = enum.auto()
    """When adding arguments for a dataclass that has previously been added, the arguments for both
    the old and new destinations will be set using the same option_string, and the passed values
    for the old and new destinations will correspond to the first and second values, respectively.

    NOTE: This changes the argparse type for that argument into a list of the original item type.
    """


class NestedFieldDisplay(enum.Enum):
    """Controls how option strings are generated for nested fields."""

    SHORTEST = enum.auto()
    """Tries to generate short flags, with only the minimal differentiating prefix as needed."""

    FULL_PATH = enum.auto()
    """Generates arguments with their full destination path."""

    BOTH = enum.auto()
    """Generates both the flat and nested arguments."""


class DashesOrUnderscores(enum.Enum):
    """Specifies whether to prefer only '_', both '_'/'-', or only '-', for command-line flags."""

    UNDERSCORE = enum.auto()
    """Use underscores."""

    DASH = enum.auto()
    """Use only dashes in option strings."""

    BOTH = enum.auto()
    """Use both underscores and dashes in option strings."""


class ArgumentParserKwargs(TypedDict, total=False):
    prog: str | None
    usage: str | None
    description: str | None
    epilog: str | None
    parents: Sequence[ArgumentParser]
    formatter_class: argparse._FormatterClass
    prefix_chars: str
    fromfile_prefix_chars: str | None
    argument_default: Any
    conflict_handler: str
    add_help: bool
    allow_abbrev: bool
    exit_on_error: bool
    # New options:
    conflict_resolution: ConflictResolution
    """What kind of prefixing mechanism to use when reusing dataclasses (argument groups).

    For more info, check the docstring of the `ConflictResolution` Enum.
    """

    dashes_or_underscores: DashesOrUnderscores
    """Controls the formatting of the dashes in option strings.

    For example, when set to `DashesOrUnderscores.BOTH`, "--no-cache" and "--no_cache" can both be
    used to point to the same `no_cache` attribute of a dataclass.
    """

    nested_field_display: NestedFieldDisplay
    """Controls how the option strings of nested arguments are generated."""

    add_config_path_arg: bool | None

    config_path: Path | str | Sequence[Path | str] | None
    """When set to `True`, adds a `--config_path` argument used to select a config file to load."""

    remove_root_from_option_strings: bool
    """Whether to remove the root name from the option strings when there is only one dataclass.

    This can be useful when there is only one dataclass added to the parser, so that instead of
    passing --config.model.learning_rate=0.1, you can just pass --model.learning_rate=0.1.
    """
