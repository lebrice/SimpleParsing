"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
from __future__ import annotations

import argparse
from collections.abc import Callable
import copy
import dataclasses
import functools
import inspect
import shlex
import sys
from argparse import (
    HelpFormatter,
    Namespace,
)
from logging import getLogger
from pathlib import Path
from typing import Any, Callable, Literal, Sequence, TypeVar, Unpack

from .conflicts import ConflictResolution
from .help_formatter import SimpleHelpFormatter
from .utils import (
    Dataclass,
    DataclassT,
)
from .types import (
    ArgparseParserState,
    GeneratedAddArgumentKwargs,
    ParserState,
    ParserOptions,
    AddedDcArguments,
    AddArgumentKwargs,
    AddArgumentGroupKwargs,
    FieldMetaData,
)

logger = getLogger(__name__)

T = TypeVar("T")


class ParsingError(RuntimeError, SystemExit):
    pass


ArgparseGroupsAndActionKwargs = list[
    tuple[AddArgumentGroupKwargs, list[GeneratedAddArgumentKwargs]]
]


def preprocess(
    parser_state: ParserState, args: Sequence[str], namespace: Namespace
) -> argparse.ArgumentParser:
    argparse_groups_and_action_kwargs = convert_to_argparse(
        parser_state, args=args, namespace=namespace
    )

    while there_are_unresolved_subgroups(
        parser_state, argparse_groups_and_action_kwargs, args, namespace
    ) or there_are_conflicts(parser_state, argparse_groups_and_action_kwargs):
        parser_state = resolve_subgroups(parser_state, args=args, namespace=namespace)
        parser_state = resolve_conflicts(parser_state, args=args, namespace=namespace)
        argparse_groups_and_action_kwargs = convert_to_argparse(
            parser_state, args=args, namespace=namespace
        )

    # Everything is done. We can now finally add all the arguments and parse them.
    parser = set_state(argparse.ArgumentParser(), parser_state)
    for arg_group_kwargs, field_args_list in argparse_groups_and_action_kwargs:
        arg_group = parser.add_argument_group(**arg_group_kwargs)
        for field_args in field_args_list:
            arg_group.add_argument(*field_args.pop("option_strings"), **field_args)
    return parser


def there_are_unresolved_subgroups(
    parser_state: ParserState,
    groups_to_fields: ArgparseGroupsAndActionKwargs,
    args: Sequence[str],
    namespace: Namespace,
) -> bool:
    for dataclass_args in parser_state.added_dc_args:
        dataclass = dataclass_args.dataclass
        # for field in dataclasses.fields(dataclass)
    return False  # TODO


def there_are_conflicts(
    parser_state: ParserState, argparse_groups_and_action_kwargs: ArgparseGroupsAndActionKwargs
) -> bool:
    all_destinations: set[str] = set()
    for _, field_actions_kwargs in argparse_groups_and_action_kwargs:
        for add_argument_kwargs in field_actions_kwargs:
            field_destination = add_argument_kwargs["dest"]
            if field_destination in all_destinations:
                return True
            all_destinations.add(field_destination)
    return False


def resolve_subgroups(
    parser_state: ParserState, args: Sequence[str], namespace: Namespace
) -> ParserState:
    ...


def resolve_conflicts(
    parser_state: ParserState, args: Sequence[str], namespace: Namespace
) -> ParserState:
    ...


def convert_to_argparse(
    parser_state: ParserState, args: Sequence[str], namespace: Namespace
) -> ArgparseGroupsAndActionKwargs:
    # NOTE: There are no more conflicts
    result: ArgparseGroupsAndActionKwargs = []

    dc_args: AddedDcArguments
    for dc_args in parser_state.added_dc_args:
        # For each dataclass that was added?
        arg_group_kwargs: AddArgumentGroupKwargs = argparse_group_for_dataclass(dc_args)
        field_args_list: list[AddArgumentKwargs] = argparse_args_for_fields_of(dc_args)

        result.append((arg_group_kwargs, field_args_list))
    return result


def set_state(
    parser: argparse.ArgumentParser, state: ArgparseParserState
) -> argparse.ArgumentParser:
    ...


class ArgumentParser(argparse.ArgumentParser):
    """Subclass of `argparse.ArgumentParser` that also creates argument groups from dataclasses."""

    def __init__(
        self,
        prog: str | None = None,
        usage: str | None = None,
        description: str | None = None,
        epilog: str | None = None,
        parents: Sequence[ArgumentParser] = (),
        formatter_class: argparse._FormatterClass = SimpleHelpFormatter,
        prefix_chars: str = "-",
        fromfile_prefix_chars: str | None = None,
        argument_default: Any = None,
        conflict_handler: str = "error",
        add_help: bool = True,
        allow_abbrev: bool = True,
        exit_on_error: bool = True,
        conflict_resolution: ConflictResolution = ConflictResolution.AUTO,
        add_option_string_dash_variants: DashVariant = DashVariant.AUTO,
        argument_generation_mode=ArgumentGenerationMode.FLAT,
        nested_mode: NestedMode = NestedMode.DEFAULT,
        add_config_path_arg: bool | None = None,
        config_path: Path | str | Sequence[Path | str] | None = None,
    ):
        """Creates an ArgumentParser instance.

        Parameters
        =============
        - prog: The name of the program (default: ``os.path.basename(sys.argv[0])``)
        - usage: A usage message (default: auto-generated from arguments)
        - description: A description of what the program does
        - epilog: Text following the argument descriptions
        - parents: Parsers whose arguments should be copied into this one
        - formatter_class: HelpFormatter class for printing help messages
        - prefix_chars: Characters that prefix optional arguments
        - fromfile_prefix_chars: Characters that prefix files containing additional arguments
        - argument_default: The default value for all arguments
        - conflict_handler: String indicating how to handle conflicts
        - add_help: Add a -h/-help option
        - allow_abbrev: Allow long options to be abbreviated unambiguously
        - exit_on_error: Determines whether or not ArgumentParser exits with error info when an \
            error occurs
        - conflict_resolution: What kind of prefixing mechanism to use when reusing dataclasses \
            (argument groups). For more info, check the docstring of the `ConflictResolution` Enum.
        - add_option_string_dash_variants: Controls the formatting of the dashes in option strings.
            This sets whether or not to add option_string variants where the underscores in
            attribute names are replaced with dashes.
            
            For example, when set to DashVariant.UNDERSCORE_AND_DASH, "--no-cache" and "--no_cache"
            can both be used to point to the same attribute `no_cache` on some dataclass.
        - argument_generation_mode:  Controls how option strings of nested arguments are generated.
    
            In the `ArgumentGenerationMode.FLAT` mode, the default one, the arguments are flat when
            possible, ignoring their nested structure and including it only on the presence of a
            conflict.

            In the `ArgumentGenerationMode.NESTED` mode, the option strings always show the full
            path, to show their nested structure.

            In the `ArgumentGenerationMode.BOTH` mode, both option strings are generated for each
            argument.
        - nested_mode: Controls option strings generation with `argument_generation_mode!=FLAT`.
    
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
        - formatter_class: The formatter class to use.
    
            By default, uses `simple_parsing.SimpleHelpFormatter`, which is a combination of the
            `argparse.ArgumentDefaultsHelpFormatter`, `argparse.MetavarTypeHelpFormatter` and
            `argparse.RawDescriptionHelpFormatter` classes.

        - add_config_path_arg: Whether to add an argument to select a config file to load.
            
            When set to `True`, adds a `--config_path` argument of type `Path`, which accepts more
            than one value, allowing you to specify one or more configuration files that should be
            loaded and used as default values.
        """
        super().__init__(
            prog=prog,
            usage=usage,
            description=description,
            epilog=epilog,
            parents=parents,
            formatter_class=formatter_class,
            prefix_chars=prefix_chars,
            fromfile_prefix_chars=fromfile_prefix_chars,
            argument_default=argument_default,
            conflict_handler=conflict_handler,
            add_help=add_help,
            allow_abbrev=allow_abbrev,
            exit_on_error=exit_on_error,
        )
        self.conflict_resolution = conflict_resolution
        self.add_option_string_dash_variants = add_option_string_dash_variants
        self.argument_generation_mode = argument_generation_mode
        self.nested_mode = nested_mode
        self.add_help = add_help
        self.config_path = config_path
        self.config_paths: list[Path] = []
        if isinstance(config_path, (str, Path)):
            self.config_paths.append(Path(config_path))
        elif config_path is not None:
            self.config_paths.extend(Path(p) for p in config_path)
        if add_config_path_arg is None:
            # By default, add a config path argument if a config path was passed.
            add_config_path_arg = bool(config_path)
        self.add_config_path_arg = add_config_path_arg

        self._added_dc_arguments: list[AddedDcArguments] = []

    def add_arguments(
        self,
        dataclass: type[DataclassT] | DataclassT,
        dest: str,
        *,
        prefix: str = "",
        default: DataclassT | None = None,
    ) -> None:
        """Adds command-line arguments for the fields of `dataclass`.

        Parameters
        ----------
        dataclass : Union[Type[Dataclass], Dataclass]
            The dataclass whose fields are to be parsed from the command-line.
            If an instance of a dataclass is given, it is used as the default
            value if none is provided.
        dest : str
            The destination attribute of the `argparse.Namespace` where the
            dataclass instance will be stored after calling `parse_args()`
        prefix : str, optional
            An optional prefix to add prepend to the names of the argparse
            arguments which will be generated for this dataclass.
            This can be useful when registering multiple distinct instances of
            the same dataclass, by default ""
        default : Dataclass, optional
            An instance of the dataclass type to get default values from, by
            default None
        dataclass_wrapper_class : Type[DataclassWrapper], optional
            The type of `DataclassWrapper` to use for this dataclass. This can be used to customize
            how the arguments are generated. However, I'd suggest making a GitHub issue if you find
            yourself using this often.

        Returns
        -------
        The generated DataclassWrapper instance. Feel free to inspect / play around with this if
        you want :)
        """
        self._added_dc_arguments.append(
            AddedDcArguments(dataclass=dataclass, dest=dest, prefix=prefix, default=default)
        )

    def parse_known_args(
        self,
        args: Sequence[str] | None = None,
        namespace: Namespace | None = None,
    ) -> tuple[Namespace, list[str]]:
        args = sys.argv[1:] if args is None else list(args)
        namespace = Namespace() if namespace is None else namespace

        _parser: argparse.ArgumentParser = self._preprocessing(args=args, namespace=namespace)
        # NOTE: NOT RECURSIVE!
        parsed_args, unparsed_args = _parser.parse_known_args(args=args, namespace=namespace)

        parsed_args, unparsed_args = self._postprocessing(parsed_args, unparsed_args)
        return parsed_args, unparsed_args

    def print_help(self, file=None, args: Sequence[str] | None = None):
        _parser = self._preprocessing(args=list(args) if args else [], namespace=Namespace())
        return _parser.print_help(file)

    def _preprocessing(self, args: Sequence[str], namespace: Namespace) -> argparse.ArgumentParser:
        # 1. Resolve subgroups choices and conflicts
        # 2. Given the Parser's state (including the AddedDcArguments), the `args` and `namespace`:
        #   - Create the AddArgumentGroupKwargs for each dataclass
        #   - Create the AddArgumentKwargs for each field of each dataclass
        ...
        return preprocess(self.state, args, namespace)

    def _postprocessing(
        self, parsed_args: Namespace, unparsed_args: Sequence[str]
    ) -> tuple[Namespace, list[str]]:
        # Create the dataclass instances by consuming values from `parsed_args`
        ...

    def clone(self):
        new = type(self)(**dict(self._get_kwargs()))
        new._add_container_actions(self)
        for dc_args in self._added_dc_arguments:
            new.add_arguments(
                dc_args.dataclass,
                dest=dc_args.dest,
                prefix=dc_args.prefix,
                default=dc_args.default,
            )
        return new

    @property
    def state(self) -> ParserState:
        """An object containing a copy of the ArgumentParser's state.

        NOTE: Modifying any of the attributes of this object will not affect the parser.
        """
        return copy.deepcopy(self._state)

    def _get_kwargs(self) -> list[tuple[str, Any]]:
        kwargs = dict(super()._get_kwargs())
        added_args = [
            (name, getattr(self, name))
            for name in inspect.signature(type(self).__init__).parameters
            if name not in kwargs and name != "self"
        ]
        return list(kwargs.items()) + added_args

    @property
    def _state(self) -> ParserState:
        """An unsafe, mutable version of this parser's state."""
        return ParserState(
            registries=self._registries.copy(),
            actions=self._actions.copy(),
            option_string_actions=self._option_string_actions.copy(),
            has_negative_number_optionals=self._has_negative_number_optionals.copy(),
            action_groups=self._action_groups.copy(),
            mutually_exclusive_groups=self._mutually_exclusive_groups.copy(),
            defaults=self._defaults.copy(),
            added_dc_args=self._added_dc_arguments.copy(),
        )


# TODO: Change the order of arguments to put `args` as the second argument.
def parse(
    config_class: type[DataclassT],
    config_path: Path | str | None = None,
    args: str | Sequence[str] | None = None,
    default: DataclassT | None = None,
    dest: str = "config",
    *,
    prefix: str = "",
    nested_mode: NestedMode = NestedMode.WITHOUT_ROOT,
    conflict_resolution: ConflictResolution = ConflictResolution.AUTO,
    add_option_string_dash_variants: DashVariant = DashVariant.AUTO,
    argument_generation_mode=ArgumentGenerationMode.FLAT,
    formatter_class: type[HelpFormatter] = SimpleHelpFormatter,
    add_config_path_arg: bool | None = None,
    **kwargs,
) -> DataclassT:
    """Parse the given dataclass from the command-line.

    See the `ArgumentParser` constructor for more details on the arguments (they are the same here
    except for `nested_mode`, which has a different default value).

    If `config_path` is passed, loads the values from that file and uses them as defaults.
    """
    parser = ArgumentParser(
        nested_mode=nested_mode,
        add_help=True,
        # add_config_path_arg=None,
        config_path=config_path,
        conflict_resolution=conflict_resolution,
        add_option_string_dash_variants=add_option_string_dash_variants,
        argument_generation_mode=argument_generation_mode,
        formatter_class=formatter_class,
        add_config_path_arg=add_config_path_arg,
        **kwargs,
    )

    parser.add_arguments(config_class, prefix=prefix, dest=dest, default=default)

    if isinstance(args, str):
        args = shlex.split(args)
    parsed_args = parser.parse_args(args)

    config: Dataclass = getattr(parsed_args, dest)
    return config


def parse_known_args(
    config_class: type[Dataclass],
    config_path: Path | str | None = None,
    args: str | Sequence[str] | None = None,
    default: Dataclass | None = None,
    dest: str = "config",
    *,
    nested_mode: NestedMode = NestedMode.WITHOUT_ROOT,
    conflict_resolution: ConflictResolution = ConflictResolution.AUTO,
    add_option_string_dash_variants: DashVariant = DashVariant.AUTO,
    argument_generation_mode=ArgumentGenerationMode.FLAT,
    formatter_class: type[HelpFormatter] = SimpleHelpFormatter,
    add_config_path_arg: bool | None = None,
) -> tuple[Dataclass, list[str]]:
    """Parse the given dataclass from the command-line, returning the leftover arguments.

    See the `ArgumentParser` constructor for more details on the arguments (they are the same here
    except for `nested_mode`, which has a different default value).

    If `config_path` is passed, loads the values from that file and uses them as defaults.
    """

    if isinstance(args, str):
        args = shlex.split(args)
    parser = ArgumentParser(
        nested_mode=nested_mode,
        add_help=True,
        # add_config_path_arg=None,
        config_path=config_path,
        conflict_resolution=conflict_resolution,
        add_option_string_dash_variants=add_option_string_dash_variants,
        argument_generation_mode=argument_generation_mode,
        formatter_class=formatter_class,
        add_config_path_arg=add_config_path_arg,
    )
    parser.add_arguments(config_class, dest=dest, default=default)
    parsed_args, unknown_args = parser.parse_known_args(args)
    config: Dataclass = getattr(parsed_args, dest)
    return config, unknown_args


def field(
    *,
    default: T | Literal[dataclasses.MISSING] = dataclasses.MISSING,
    default_factory: Callable[[], T] | Literal[dataclasses.MISSING] = dataclasses.MISSING,
    init: bool = True,
    repr: bool = True,
    hash: bool | None = None,
    compare: bool = True,
    metadata: dict[str, Any] | None = None,
    # Added arguments:
    alias: str | list[str] | None = None,
    cmd: bool = True,
    positional: bool = False,
    to_dict: bool = True,
    encoding_fn: Callable[[T], Any] | None = None,
    decoding_fn: Callable[[Any], T] | None = None,
    # dataclasses.field arguments
    **add_argument_overrides: Unpack[AddArgumentKwargs[T]],
) -> T:
    # metadata = metadata.copy() if metadata else {}
    _metadata: FieldMetaData[T] = (metadata or {}).copy()  # type: ignore
    _metadata.update(
        {
            "alias": [alias] if isinstance(alias, str) else alias or [],
            "to_dict": to_dict,
            "encoding_fn": encoding_fn,
            "decoding_fn": decoding_fn,
            "cmd": cmd,
            "positional": positional,
            "add_argument_overrides": add_argument_overrides,
        }
    )

    if add_argument_overrides:
        action = add_argument_overrides.get("action")
        if action == "store_false":
            if default not in {dataclasses.MISSING, True}:
                raise RuntimeError(
                    "default should either not be passed or set "
                    "to True when using the store_false action."
                )
            default = True  # type: ignore
        elif action == "store_true":
            if default not in {dataclasses.MISSING, False}:
                raise RuntimeError(
                    "default should either not be passed or set "
                    "to False when using the store_true action."
                )
            default = False  # type: ignore
    # NOTE: Adding the three branches to narrowing down the types and match the three overloads of
    # dataclasses.field
    if default is not dataclasses.MISSING:
        return dataclasses.field(  # type: ignore
            default=default,
            init=init,
            repr=repr,
            hash=hash,
            compare=compare,
            metadata=_metadata,
        )
    elif not isinstance(default_factory, dataclasses._MISSING_TYPE):
        return dataclasses.field(
            default_factory=default_factory,
            init=init,
            repr=repr,
            hash=hash,
            compare=compare,
            metadata=_metadata,
        )
    else:
        return dataclasses.field(
            init=init, repr=repr, hash=hash, compare=compare, metadata=_metadata
        )
