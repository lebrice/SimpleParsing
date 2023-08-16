from __future__ import annotations

import argparse
import dataclasses
from argparse import (
    Action,
    HelpFormatter,
)
from collections.abc import Callable, Iterable
from typing import Any, Generic, Literal, Sequence, Type, TypeVar, Required, TypedDict
import enum


from .conflicts import ConflictResolution
from .utils import DataclassT

T = TypeVar("T")


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
    added_dc_args: Sequence[AddedDcArguments]


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


class ArgumentGenerationMode(enum.Enum):
    """
    Enum for argument generation modes.
    """

    FLAT = enum.auto()
    """ Tries to generate flat arguments, removing the argument destination path when possible. """

    NESTED = enum.auto()
    """ Generates arguments with their full destination path. """

    BOTH = enum.auto()
    """ Generates both the flat and nested arguments. """


class NestedMode(enum.Enum):
    """
    Controls how nested arguments are generated.
    """

    DEFAULT = enum.auto()
    """ By default, the full destination path is used. """

    WITHOUT_ROOT = enum.auto()
    """
    The full destination path is used, but the first level is removed.
    Useful because sometimes the first level is uninformative (i.e. 'args').
    """


class DashVariant(enum.Enum):
    """Specifies whether to prefer only '_', both '_'/'-', or only '-', for cmd-line-flags.

    - AUTO (default):
        Currently, UNDERSCORE.

    - UNDERSCORE:

    - UNDERSCORE_AND_DASH:

    - DASH:

    """

    AUTO = False
    UNDERSCORE = False
    UNDERSCORE_AND_DASH = True
    DASH = "only"


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class ParserOptions:
    conflict_resolution: ConflictResolution
    """What kind of prefixing mechanism to use when reusing dataclasses (argument groups).
    For more info, check the docstring of the `ConflictResolution` Enum.
    """

    add_option_string_dash_variants: DashVariant
    """Controls the formatting of the dashes in option strings.
    
    Whether or not to add option_string variants where the underscores in attribute names are
    replaced with dashes.
    
    For example, when set to DashVariant.UNDERSCORE_AND_DASH, "--no-cache" and "--no_cache" can
    both be used to point to the same attribute `no_cache` on some dataclass.
    """

    argument_generation_mode: ArgumentGenerationMode
    """Controls how the option strings of nested arguments are generated.
    
    In the ArgumentGenerationMode.FLAT mode, the default one, the arguments are flat when possible,
    ignoring their nested structure and including it only on the presence of a
    conflict.

    In the ArgumentGenerationMode.NESTED mode, the option strings always show the full path, to
    show their nested structure.

    In the ArgumentGenerationMode.BOTH mode, both option strings are generated for each argument.
    """

    nested_mode: NestedMode
    """Controls how option strings are generated when using a `argument_generation_mode!=FLAT`.
    
    (ArgumentGenerationMode.NESTED and ArgumentGenerationMode.BOTH)
    In the NestedMode.DEFAULT mode, the nested arguments are generated
    reflecting their full 'destination' path from the returning namespace.

    In the NestedMode.WITHOUT_ROOT, the first level is removed. This is useful when
    parser.add_arguments is only called once, and where the same prefix would be shared
    by all arguments. For example, if you have a single dataclass MyArguments and
    you call parser.add_arguments(MyArguments, "args"), the arguments could look like this:
    '--args.input.path --args.output.path'.
    We could prefer to remove the root level in such a case
        so that the arguments get generated as
    '--input.path --output.path'.
    """

    formatter_class: Type[HelpFormatter]
    """ The formatter class to use.
    
    By default, uses `simple_parsing.SimpleHelpFormatter`, which is a combination of the
    `argparse.ArgumentDefaultsHelpFormatter`, `argparse.MetavarTypeHelpFormatter` and
    `argparse.RawDescriptionHelpFormatter` classes.
    """

    add_config_path_arg: bool
    """When set to `True`, adds a `--config_path` argument used to select a config file to load."""
