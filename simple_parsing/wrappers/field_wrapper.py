from __future__ import annotations

import argparse
import dataclasses
import inspect
import sys
import typing
from collections.abc import Hashable
from enum import Enum, auto
from logging import getLogger
from typing import Any, Callable, ClassVar, Union, cast

from typing_extensions import Literal

from simple_parsing.help_formatter import TEMPORARY_TOKEN

from .. import docstring, utils
from ..helpers.custom_actions import BooleanOptionalAction
from ..utils import Dataclass
from .field_metavar import get_metavar
from .field_parsing import get_parsing_fn
from .wrapper import Wrapper

if typing.TYPE_CHECKING:
    from simple_parsing import ArgumentParser

    from .dataclass_wrapper import DataclassWrapper

logger = getLogger(__name__)


class ArgumentGenerationMode(Enum):
    """Enum for argument generation modes."""

    FLAT = auto()
    """Tries to generate flat arguments, removing the argument destination path when possible."""

    NESTED = auto()
    """Generates arguments with their full destination path."""

    BOTH = auto()
    """Generates both the flat and nested arguments."""


class NestedMode(Enum):
    """Controls how nested arguments are generated."""

    DEFAULT = auto()
    """By default, the full destination path is used."""

    WITHOUT_ROOT = auto()
    """The full destination path is used, but the first level is removed.

    Useful because sometimes the first level is uninformative (i.e. 'args').
    """


class DashVariant(Enum):
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


class FieldWrapper(Wrapper):
    """The FieldWrapper class acts a bit like an 'argparse.Action' class, which essentially just
    creates the `option_strings` and `arg_options` that get passed to the
    `add_argument(*option_strings, **arg_options)` function of the `argparse._ArgumentGroup` (in
    this case represented by the `parent` attribute, an instance of the class `DataclassWrapper`).

    The `option_strings`, `required`, `help`, `metavar`, `default`, etc.
    attributes just autogenerate the argument of the same name of the
    above-mentioned `add_argument` function. The `arg_options` attribute fills
    in the rest and may overwrite these values, depending on the type of field.

    The `field` argument is the actually wrapped `dataclasses.Field` instance.
    """

    # Whether or not `simple_parsing` should add option_string variants where
    # underscores in attribute names are replaced with dashes.
    # For example, when set to DashVariant.UNDERSCORE_AND_DASH,
    #   "--no-cache" and "--no_cache" could both
    # be used to point to the same attribute `no_cache` on some dataclass.
    # TODO: This can often make "--help" messages a bit crowded
    add_dash_variants: ClassVar[DashVariant] = DashVariant.AUTO

    # Whether to follow a flat or nested argument structure.
    argument_generation_mode: ClassVar[ArgumentGenerationMode] = ArgumentGenerationMode.FLAT

    # Controls how nested arguments are generated.
    nested_mode: ClassVar[NestedMode] = NestedMode.DEFAULT

    def __init__(
        self, field: dataclasses.Field, parent: DataclassWrapper | None = None, prefix: str = ""
    ):
        super().__init__()
        self.field: dataclasses.Field = field
        self.prefix: str = prefix
        self._parent: Any = parent
        # Holders used to 'cache' the properties.
        # (could've used cached_property with Python 3.8).
        self._option_strings: set[str] | None = None
        self._required: bool | None = None

        try:
            self._docstring = docstring.get_attribute_docstring(
                self.parent.dataclass, self.field.name
            )
        except (SystemExit, Exception) as e:
            logger.debug(f"Couldn't find attribute docstring for field {self.name}, {e}")
            self._docstring = docstring.AttributeDocString()

        self._help: str | None = None
        self._metavar: str | None = None
        self._default: Any | list[Any] | None = None
        self._dest: str | None = None
        # the argparse-related options:
        self._arg_options: dict[str, Any] = {}
        self._dest_field: FieldWrapper | None = None
        self._type: type[Any] | None = None

        # stores the resulting values for each of the destination attributes.
        self._results: dict[str, Any] = {}

    @property
    def arg_options(self) -> dict[str, Any]:
        """Dictionary of values to be passed to the `add_argument` method.

        The main feature of this package is to infer these arguments
        automatically using features of the built-in `dataclasses` package, as
        well as Python's type annotations.

        By passing additional keyword arguments to the `field()`
        function, the autogenerated arguments can be overwritten,
        giving access to all of the usual argparse features know and love.

        NOTE: When passing an `action` keyword argument, we remove all the
        autogenerated options that aren't required by the Action class
        constructor.
        For example, when specifying a custom `action` like "store_true" or
        "store_false", the `type` argument autogenerated here shouldn't be
        passed to the constructor of the `argparse._StoreFalseAction`, so we
        discard it.
        """
        if self._arg_options:
            return self._arg_options
        # get the auto-generated options.
        options = self.get_arg_options()
        # overwrite the auto-generated options with given ones, if any.
        options.update(self.custom_arg_options)
        # only keep the arguments used by the Action constructor.
        action = options.get("action", "store")
        self._arg_options = only_keep_action_args(options, action)
        return self._arg_options

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Any,
        constructor_arguments: dict[str, dict[str, Any]],
        option_string: str | None = None,
    ):
        """Immitates a custom Action, which sets the corresponding value from `values` at the right
        destination in the `constructor_arguments` of the parser.

        TODO: Doesn't seem currently possible to check whether the argument was passed in the
        first place.

        Args:
            parser (argparse.ArgumentParser): the `simple_parsing.ArgumentParser` used.
            namespace (argparse.Namespace): (unused).
            values (Any): The parsed values for the argument.
            constructor_arguments: The dict of constructor arguments for each dataclass.
            option_string (Optional[str], optional): (unused). Defaults to None.
        """
        from simple_parsing import ArgumentParser

        parser = cast(ArgumentParser, parser)

        if self.is_reused:
            values = self.duplicate_if_needed(values)
            logger.debug(f"(replicated the parsed values: '{values}')")
        else:
            values = [values]

        self._results = {}

        for destination, value in zip(self.destinations, values):
            if self.is_subgroup:
                logger.debug(f"Ignoring the FieldWrapper for subgroup at dest {self.dest}")
                return

            parent_dest, attribute = utils.split_dest(destination)
            value = self.postprocess(value)

            self._results[destination] = value

            # if destination.endswith(f"_{i}"):
            #     attribute = attribute[:-2]
            #     constructor_arguments[parent_dest][attribute] = value

            # TODO: Need to decide which one to do here. Seems easier to always set all the values.
            logger.debug(f"constructor_arguments[{parent_dest}][{attribute}] = {value}")
            constructor_arguments[parent_dest][attribute] = value

            if self.is_subgroup:
                if not hasattr(namespace, "subgroups"):
                    namespace.subgroups = {}

                if isinstance(value, str) and value in self.subgroup_choices.keys():
                    # We've just parsed the name of the chosen subgroup.
                    # NOTE: There can't be any ambiguity here, since the keys of the dictionary are
                    # string, and the values are always dataclass types. We don't need to worry
                    # about having to deal with {"bob": "alice", "alice": "foo"}-type weirdness.
                    namespace.subgroups[self.dest] = value
                    logger.debug(f"Chosen subgroup for '{self.dest}':  '{value}'")

    def get_arg_options(self) -> dict[str, Any]:
        """Create the `parser.add_arguments` kwargs for this field.

        TODO: Refactor this, following https://github.com/lebrice/SimpleParsing/issues/150
        """
        if not self.field.init:
            # Don't add command-line arguments for fields that have `init=False`.
            return {}
        _arg_options: dict[str, Any] = {}

        # Not sure why, but argparse doesn't allow using a different dest for a positional arg.
        # _Appears_ trivial to support within argparse.
        if not self.field.metadata.get("positional"):
            _arg_options["required"] = self.required
            _arg_options["dest"] = self.dest
        elif not self.required:
            # For positional arguments that aren't required we need to set
            # nargs='?' to make them optional.
            _arg_options["nargs"] = "?"
        _arg_options["default"] = self.default
        _arg_options["metavar"] = get_metavar(self.type)

        if self.help:
            _arg_options["help"] = self.help
        elif self.default is not None:
            # issue 64: Need to add a temporary 'help' string, so that the formatter
            # automatically adds the (default: '123'). We then remove it.
            _arg_options["help"] = TEMPORARY_TOKEN

        # TODO: Possible duplication between utils.is_foo(Field) and self.is_foo where foo in
        # [choice, optional, list, tuple, dataclass, etc.]
        if self.is_choice:
            choices = self.choices
            assert choices
            item_type = str
            _arg_options["type"] = item_type
            _arg_options["choices"] = choices
            # TODO: Refactor this. is_choice and is_list are both contributing, so it's unclear.
            if utils.is_list(self.type):
                _arg_options["nargs"] = argparse.ZERO_OR_MORE
            # We use the default 'metavar' generated by argparse.
            _arg_options.pop("metavar", None)

        elif utils.is_optional(self.type) or self.field.default is None:
            if not self.field.metadata.get("positional"):
                _arg_options["required"] = False

            if utils.is_optional(self.type):
                type_arguments = utils.get_args(self.type)
                # NOTE: Optional[<something>] is always translated to
                # Union[<something>, NoneType]
                assert type_arguments
                non_none_types = [
                    t
                    for t in type_arguments
                    if t is not type(None)  # noqa: E721
                ]  # noqa: E721
                assert non_none_types
                if len(non_none_types) == 1:
                    wrapped_type = non_none_types[0]
                else:
                    # Construct the type annotation for the non-optional version of the type.
                    wrapped_type = Union[tuple(non_none_types)]  # type: ignore
            else:
                assert self.field.default is None
                # If the default value is None, then type annotation is incorrect (i.e. not
                # `Optional[T]` or `T | None`). We allow it, as discussed in issue #132:
                # https://github.com/lebrice/SimpleParsing/issues/132, and treat the type
                # annotation as the type of the field.
                wrapped_type = self.type

            if utils.is_tuple(wrapped_type):
                # TODO: ISSUE 42: better handle optional/nested tuples.
                # For now we just assume that the item types are 'simple'.

                # IDEA: This could probably be a static method that takes in the type
                # annotation, and uses a recursive call to fetch the arg options of the
                # item type, and uses some of the entries from that dict to construct
                # the arg options of the parent?
                # NOTE: We'd have to return different value for the `type` argument
                # depending on the nesting:
                # Tuple[int, int] -> <class int>
                # Tuple[int, str] -> <some autogenerated function>
                # Tuple[Tuple[int, str], Tuple[int, str]] -> <some autogenerated
                #   function *that doesn't just use `<class int> from above twice!
                #   (Since we want to support passing --foo '(a, 1)' '(b, 4)'
                # `)>
                _arg_options["type"] = get_parsing_fn(wrapped_type)
                _arg_options["nargs"] = utils.get_container_nargs(wrapped_type)

            elif utils.is_list(wrapped_type):
                _arg_options["type"] = utils.get_argparse_type_for_container(wrapped_type)
                _arg_options["nargs"] = "*"
                # NOTE: Can't set 'const', since we'd get:
                # ValueError: nargs must be '?' to supply const
                # _arg_options["const"] = []
            else:
                _arg_options["type"] = get_parsing_fn(wrapped_type)
                # TODO: Should the 'nargs' really be '?' here?
                _arg_options["nargs"] = "?"

        elif self.is_union:
            logger.debug("Parsing a Union type!")
            _arg_options["type"] = get_parsing_fn(self.type)

        elif self.is_enum:
            logger.debug(f"Adding an Enum attribute '{self.name}'")
            # we actually parse enums as string, and convert them back to enums
            # in the `process` method.
            logger.debug(f"self.choices = {self.choices}")
            assert issubclass(self.type, Enum)
            _arg_options["choices"] = list(e.name for e in self.type)
            _arg_options["type"] = str
            # if the default value is an Enum, we convert it to a string.
            if self.default:

                def enum_to_str(e):
                    return e.name if isinstance(e, Enum) else e

                if self.is_reused:
                    _arg_options["default"] = [enum_to_str(default) for default in self.default]
                else:
                    _arg_options["default"] = enum_to_str(self.default)

        elif self.is_list:
            logger.debug(f"Adding a List attribute '{self.name}': {self.type}")
            _arg_options["nargs"] = "*"

            if self.is_reused:
                # TODO: Only the 'single-level' lists (not reused) use the new
                # `get_parsing_fn` function (for now).
                type_fn = utils._parse_multiple_containers(self.type)
                type_fn.__name__ = utils.get_type_name(self.type)
                _arg_options["type"] = type_fn
            else:
                _arg_options["type"] = utils.get_argparse_type_for_container(self.type)

        elif utils.is_tuple(self.type):
            logger.debug(f"Adding a Tuple attribute '{self.name}' with type {self.type}")
            _arg_options["nargs"] = utils.get_container_nargs(self.type)
            _arg_options["type"] = get_parsing_fn(self.type)

            if self.is_reused:
                type_fn = utils._parse_multiple_containers(self.type)
                type_fn.__name__ = utils.get_type_name(self.type)
                _arg_options["type"] = type_fn

        elif utils.is_bool(self.type):
            if self.is_reused:
                _arg_options["type"] = utils.str2bool
                _arg_options["type"].__name__ = "bool"
                _arg_options["metavar"] = "bool"
                _arg_options["nargs"] = "?"
            else:
                # NOTE: also pass the prefix to the boolean optional action, because it needs to add it
                # to the generated negative flags as well.
                _arg_options["action"] = BooleanOptionalAction
                _arg_options["_conflict_prefix"] = self.prefix

        else:
            # "Plain" / simple argument.
            # For the metavar, use a custom passed value, if present, else do
            # not put any value in (which uses the usual value from argparse).
            if self.metavar:
                _arg_options["metavar"] = self.metavar
            else:
                # Remove the 'metavar' that we auto-generated above.
                _arg_options.pop("metavar", None)
            _arg_options["type"] = self.custom_arg_options.get("type", get_parsing_fn(self.type))

        if self.is_reused:
            if self.required:
                _arg_options["nargs"] = "+"
            else:
                _arg_options["nargs"] = "*"

        return _arg_options

    def duplicate_if_needed(self, parsed_values: Any) -> list[Any]:
        """Duplicates the passed argument values if needed, such that each instance gets a value.

        For example, if we expected 3 values for an argument, and a single value was passed,
        then we duplicate it so that each of the three instances get the same value.

        Args:
            parsed_values (Any): The parsed value(s)

        Raises:
            utils.InconsistentArgumentError: If the number of arguments passed is
            inconsistent (neither 1 or the number of instances)

        Returns:
            List[Any]: The list of parsed values, of the right length.
        """
        num_instances_to_parse = len(self.destinations)
        logger.debug(f"num to parse: {num_instances_to_parse}")
        logger.debug(f"(raw) parsed values: '{parsed_values}'")

        assert self.is_reused
        assert (
            num_instances_to_parse > 1
        ), "multiple is true but we're expected to instantiate only one instance"

        if utils.is_list(self.type) and isinstance(parsed_values, tuple):
            parsed_values = list(parsed_values)

        if not self.is_tuple and not self.is_list and isinstance(parsed_values, list):
            nesting_level = utils.get_nesting_level(parsed_values)
            if (
                nesting_level == 2
                and len(parsed_values) == 1
                and len(parsed_values[0]) == num_instances_to_parse
            ):
                result: list = parsed_values[0]
                return result

        if not isinstance(parsed_values, (list, tuple)):
            parsed_values = [parsed_values]

        if len(parsed_values) == num_instances_to_parse:
            return parsed_values
        elif len(parsed_values) == 1:
            return parsed_values * num_instances_to_parse
        else:
            raise utils.InconsistentArgumentError(
                f"The field '{self.name}' contains {len(parsed_values)} values,"
                f" but either 1 or {num_instances_to_parse} values were "
                f"expected."
            )

    def postprocess(self, raw_parsed_value: Any) -> Any:
        """Applies any conversions to the 'raw' parsed value before it is used in the constructor
        of the dataclass.

        Args:
            raw_parsed_value (Any): The 'raw' parsed value.

        Returns:
            Any: The processed value
        """
        if self.is_enum:
            logger.debug(
                f"field postprocessing for Enum field '{self.name}' with value:"
                f" {raw_parsed_value}'"
            )
            if isinstance(raw_parsed_value, str):
                raw_parsed_value = self.type[raw_parsed_value]  # type: ignore
            return raw_parsed_value

        elif self.is_choice:
            choice_dict = self.choice_dict
            if choice_dict:
                key_type = type(next(iter(choice_dict.keys())))
                if self.is_list and isinstance(raw_parsed_value[0], key_type):
                    return [choice_dict[value] for value in raw_parsed_value]
                elif isinstance(raw_parsed_value, key_type):
                    return choice_dict[raw_parsed_value]
            return raw_parsed_value

        elif self.is_tuple:
            logger.debug("we're parsing a tuple!")
            # argparse always returns lists by default. If the field was of a
            # Tuple type, we just transform the list to a Tuple.
            if not isinstance(raw_parsed_value, tuple):
                return tuple(raw_parsed_value)

        elif self.is_bool:
            return raw_parsed_value

        elif self.is_list:
            if isinstance(raw_parsed_value, tuple):
                return list(raw_parsed_value)
            else:
                return raw_parsed_value

        elif self.is_subparser:
            return raw_parsed_value

        elif utils.is_optional(self.type):
            item_type = utils.get_args(self.type)[0]
            if utils.is_tuple(item_type) and isinstance(raw_parsed_value, list):
                # TODO: Make sure that this doesn't cause issues with NamedTuple types.
                return tuple(raw_parsed_value)

        elif self.type not in utils.builtin_types:
            # TODO: what if we actually got an auto-generated parsing function?
            try:
                # if the field has a weird type, we try to call it directly.
                return self.type(raw_parsed_value)
            except Exception as e:
                logger.debug(
                    f"Unable to instantiate the field '{self.name}' of type "
                    f"'{self.type}' by using the type as a constructor. "
                    f"Returning the raw parsed value instead "
                    f"({raw_parsed_value}, of type {type(raw_parsed_value)}). "
                    f"(Caught Exception: {e})"
                )
                return raw_parsed_value

        logger.debug(
            f"field postprocessing for field {self.name} of type '{self.type}' and with "
            f"value '{raw_parsed_value}'"
        )
        return raw_parsed_value

    @property
    def is_reused(self) -> bool:
        return len(self.destinations) > 1

    @property
    def action(self) -> str | type[argparse.Action]:
        """The `action` argument to be passed to `add_argument(...)`."""
        return self.custom_arg_options.get("action", "store")

    @property
    def action_str(self) -> str:
        if isinstance(self.action, str):
            return self.action
        return self.action.__name__

    @property
    def custom_arg_options(self) -> dict[str, Any]:
        """Custom argparse options that overwrite those in `arg_options`.

        Can be set by using the `field` function, passing in a keyword argument
        that would usually be passed to the parser.add_argument(
        *option_strings, **kwargs) method.
        """
        return self.field.metadata.get("custom_args", {})

    @property
    def destinations(self) -> list[str]:
        return [f"{parent_dest}.{self.name}" for parent_dest in self.parent.destinations]

    @property
    def option_strings(self) -> list[str]:
        """Generates the `option_strings` argument to the `add_argument` call.

        `parser.add_argument(*name_or_flags, **arg_options)`

        ## Notes:
        - Additional names for the same argument can be added via the `field`
        function.
        - Whenever the name of an attribute includes underscores ("_"), the same
        argument can be passed by using dashes ("-") instead. This also includes
        aliases.
        - If an alias contained leading dashes, either single or double, the
        same number of dashes will be used, even in the case where a prefix is
        added.

        For an illustration of this, see the aliases example.
        """

        dashes: list[str] = []  # contains the leading dashes.
        options: list[str] = []  # contains the name following the dashes.

        def add_args(dash: str, candidates: list[str]) -> None:
            for candidate in candidates:
                options.append(candidate)
                dashes.append(dash)

        # Handle user passing us "True" or "only" directly.
        add_dash_variants = DashVariant(FieldWrapper.add_dash_variants)

        gen_mode = type(self).argument_generation_mode
        nested_mode = type(self).nested_mode

        dash = "-" if len(self.name) == 1 else "--"
        option = f"{self.prefix}{self.name}"
        nested_option = (
            self.dest if nested_mode == NestedMode.DEFAULT else ".".join(self.dest.split(".")[1:])
        )
        if add_dash_variants == DashVariant.DASH:
            option = option.replace("_", "-")
            nested_option = nested_option.replace("_", "-")

        if self.field.metadata.get("positional"):
            # Can't be positional AND have flags at same time. Also, need dest to be be this and not just option.
            return [self.dest]

        if gen_mode == ArgumentGenerationMode.FLAT:
            candidates = [option]
        elif gen_mode == ArgumentGenerationMode.NESTED:
            candidates = [nested_option]
        else:
            candidates = [option, nested_option]

        add_args(dash, candidates)

        if dash == "-":
            # also add a double-dash option:
            add_args("--", candidates)

        # add all the aliases that were passed to the `field` function.
        for alias in self.aliases:
            if alias.startswith("--"):
                dash = "--"
                name = alias[2:]
            elif alias.startswith("-"):
                dash = "-"
                name = alias[1:]
            else:
                dash = "-" if len(alias) == 1 else "--"
                name = alias
            option = f"{self.prefix}{name}"

            dashes.append(dash)
            options.append(option)

        # Additionally, add all name variants with the "_" replaced with "-".
        # For example, "--no-cache" will correctly set the `no_cache` attribute,
        # even if an alias isn't explicitly created.

        if add_dash_variants == DashVariant.UNDERSCORE_AND_DASH:
            additional_options = [option.replace("_", "-") for option in options if "_" in option]
            additional_dashes = [
                "-" if len(option) == 1 else "--" for option in additional_options
            ]
            options.extend(additional_options)
            dashes.extend(additional_dashes)

        # remove duplicates by creating a set.
        option_strings = {f"{dash}{option}" for dash, option in zip(dashes, options)}
        # TODO: possibly sort the option strings, if argparse doesn't do it
        # already.
        return list(sorted(option_strings, key=len))

    # @property
    # def prefix(self) -> str:
    #     return self._prefix

    @property
    def aliases(self) -> list[str]:
        return self.field.metadata.get("alias", [])

    @property
    def dest(self) -> str:
        """Where the attribute will be stored in the Namespace."""
        self._dest = super().dest
        # TODO: If a custom `dest` was passed, and it is a `Field` instance,
        # find the corresponding FieldWrapper and use its `dest` instead of ours.
        if self.dest_field:
            self._dest = self.dest_field.dest
            self.custom_arg_options.pop("dest", None)
        return self._dest

    @property
    def is_proxy(self) -> bool:
        return self.dest_field is not None

    @property
    def dest_field(self) -> FieldWrapper | None:
        """Return the `FieldWrapper` for which `self` is a proxy (same dest). When a `dest`
        argument is passed to `field()`, and its value is a `Field`, that indicates that this Field
        is just a proxy for another.

        In such a case, we replace the dest of `self` with that of the other wrapper's we then find
        the corresponding FieldWrapper and use its `dest` instead of ours.
        """
        if self._dest_field is not None:
            return self._dest_field
        custom_dest = self.custom_arg_options.get("dest")
        if isinstance(custom_dest, dataclasses.Field):
            all_fields: list[FieldWrapper] = []
            for parent in self.lineage():
                all_fields.extend(parent.fields)  # type: ignore
            for other_wrapper in all_fields:
                if custom_dest is other_wrapper.field:
                    self._dest_field = other_wrapper
                    break
        return self._dest_field

    @property
    def nargs(self):
        return self.custom_arg_options.get("nargs", None)

    # @property
    # def const(self):
    #     return self.custom_arg_options.get("const", None)

    @property
    def default(self) -> Any:
        """Either a single default value, when parsing a single argument, or the list of default
        values, when this argument is reused multiple times (which only happens with the
        `ConflictResolution.ALWAYS_MERGE` option).

        In order of increasing priority, this could either be:
        1. The default attribute of the field
        2. the value of the corresponding attribute on the parent,
        if it has a default value
        """

        if self.is_subgroup:
            # For subgroups, always use the subgroup_default to maintain consistency
            default = self.subgroup_default
        elif self._default is not None:
            # If a default value was set manually from the outside (e.g. from the DataclassWrapper)
            # then use that value.
            default = self._default
        elif any(
            parent_default not in (None, argparse.SUPPRESS)
            for parent_default in self.parent.defaults
        ):
            # if the dataclass with this field has a default value - either when a value was
            # passed for the `default` argument of `add_arguments` or when the parent is a nested
            # dataclass field with a default factory - we use the corresponding attribute on that
            # default instance.
            def _get_value(dataclass_default: utils.Dataclass | dict, name: str) -> Any:
                if isinstance(dataclass_default, dict):
                    return dataclass_default.get(name)
                return getattr(dataclass_default, name)

            defaults = [
                _get_value(parent_default, self.field.name)
                for parent_default in self.parent.defaults
                if parent_default not in (None, argparse.SUPPRESS)
            ]
            if len(self.parent.defaults) == 1:
                default = defaults[0]
            else:
                default = defaults
        # Try to get the default from the field, if possible.
        elif self.field.default is not dataclasses.MISSING:
            default = self.field.default
        elif self.field.default_factory is not dataclasses.MISSING:
            # Use the _default attribute to keep the result, so we can avoid calling the default
            # factory another time.
            # TODO: If the default factory is a function that returns None, it will still get
            # called multiple times. We need to set a sentinel value as the initial value of the
            # self._default attribute, so that we can correctly check whether we've already called
            # the default_factory before.
            if self._default is None:
                self._default = self.field.default_factory()
            default = self._default
        # field doesn't have a default value set.
        elif self.action == "store_true":
            default = False
        elif self.action == "store_false":
            # NOTE: The boolean parsing when default is `True` is really un-intuitive, and should
            # change in the future. See https://github.com/lebrice/SimpleParsing/issues/68
            default = True
        else:
            default = None

        # If this field is being reused, then we package up the `default` in a list.
        # TODO: Get rid of this. makes the code way uglier for no good reason.
        if self.is_reused and default is not None:
            n_destinations = len(self.destinations)
            assert n_destinations >= 1
            # BUG: This second part (the `or` part) is weird. Probably only applies when using
            # Lists of lists with the Reuse option, which is most likely not even supported..
            if utils.is_tuple_or_list(self.field.type) and len(default) != n_destinations:
                # The field is of a list type field,
                default = [default] * n_destinations
            elif not isinstance(default, list):
                default = [default] * n_destinations
            assert len(default) == n_destinations, (
                f"Not the same number of default values and destinations. "
                f"(default: {default}, # of destinations: {n_destinations})"
            )

        return default

    def set_default(self, value: Any):
        logger.debug(f"The field {self.name} has its default manually set to a value of {value}.")
        self._default = value

    @property
    def required(self) -> bool:
        if self._required is not None:
            return self._required
        if self.is_subgroup:
            return self.subgroup_default in (None, dataclasses.MISSING)
        if self.action_str.startswith("store_"):
            # all the store_* actions do not require a value.
            return False
        if self.is_optional:
            return False
        if self.parent.required:
            # if the parent dataclass is required, then this attribute is too.
            # TODO: does that make sense though?
            return True
        if self.nargs in {"?", "*"}:
            return False
        if self.nargs == "+":
            return True
        if self.default is None and argparse.SUPPRESS not in self.parent.defaults:
            return True
        if self.is_reused:
            # if we're reusing this argument, the default value might be a list
            # of `MISSING` values.
            return any(v == dataclasses.MISSING for v in self.default)
        return False

    @required.setter
    def required(self, value: bool):
        self._required = value

    @property
    def type(self) -> type[Any]:
        """Returns the wrapped field's type annotation."""
        # TODO: Refactor this. Really ugly.
        if self._type is None:
            self._type = self.field.type
            if isinstance(self._type, str):
                # The type of the field might be a string when using `from __future__ import annotations`.
                # NOTE: Here we'd like to convert the fields type to an actual type, in case the
                # `from __future__ import annotations` feature is used.
                # This should also resolve most forward references.
                from simple_parsing.annotation_utils.get_field_annotations import (
                    get_field_type_from_annotations,
                )

                field_type = get_field_type_from_annotations(
                    self.parent.dataclass, self.field.name
                )
                self._type = field_type
            elif isinstance(self._type, dataclasses.InitVar):
                self._type = self._type.type
        return self._type

    def __str__(self):
        return f"""<FieldWrapper for field '{self.dest}'>"""

    @property
    def is_choice(self) -> bool:
        return self.choices is not None

    @property
    def choices(self) -> list | None:
        """The list of possible values that can be passed on the command-line for this field, or
        None."""

        if "choices" in self.custom_arg_options:
            return self.custom_arg_options["choices"]
        if "choices" in self.field.metadata:
            return list(self.field.metadata["choices"])
        if "choice_dict" in self.field.metadata:
            return list(self.field.metadata["choice_dict"].keys())
        if utils.is_literal(self.type):
            literal_values = list(utils.get_args(self.type))
            literal_value_names = [
                v.name if isinstance(v, Enum) else str(v) for v in literal_values
            ]
            return literal_value_names
        return None

    @property
    def choice_dict(self) -> dict[str, Any] | None:
        if "choice_dict" in self.field.metadata:
            return self.field.metadata["choice_dict"]
        if utils.is_literal(self.type):
            literal_values = list(utils.get_args(self.type))
            assert literal_values, "Literal always has at least one argument."
            # We map from literal values (as strings) to the actual values.
            # e.g. from BLUE -> Color.Blue
            return {(v.name if isinstance(v, Enum) else str(v)): v for v in literal_values}
        return None

    @property
    def help(self) -> str | None:
        if self._help:
            return self._help
        if self.field.metadata.get("help"):
            return self.field.metadata.get("help")

        self._help = (
            self._docstring.docstring_below
            or self._docstring.comment_above
            or self._docstring.comment_inline
            or self._docstring.desc_from_cls_docstring
        )
        # NOTE: Need to make sure this doesn't interfere with the default value added to the help
        # string.
        if self._help == "":
            self._help = None
        return self._help

    @help.setter
    def help(self, value: str):
        self._help = value

    @property
    def metavar(self) -> str | None:
        """Returns the 'metavar' when set using one of the `field` functions, else None."""
        if self._metavar:
            return self._metavar
        self._metavar = self.custom_arg_options.get("metavar")
        return self._metavar

    @metavar.setter
    def metavar(self, value: str):
        self._metavar = value

    @property
    def name(self) -> str:
        return self.field.name

    @property
    def is_list(self):
        return utils.is_list(self.type)

    @property
    def is_enum(self) -> bool:
        return utils.is_enum(self.type)

    @property
    def is_tuple(self) -> bool:
        return utils.is_tuple(self.type)

    @property
    def is_bool(self) -> bool:
        return utils.is_bool(self.type)

    @property
    def is_optional(self) -> bool:
        return utils.is_optional(self.field.type)

    @property
    def is_union(self) -> bool:
        return utils.is_union(self.field.type)

    @property
    def is_subparser(self) -> bool:
        return utils.is_subparser_field(self.field) and "subgroups" not in self.field.metadata

    @property
    def is_subgroup(self) -> bool:
        return "subgroups" in self.field.metadata

    @property
    def subgroup_choices(self) -> dict[Hashable, Callable[[], Dataclass] | Dataclass]:
        if not self.is_subgroup:
            raise RuntimeError(f"Field {self.field} doesn't have subgroups! ")
        return self.field.metadata["subgroups"]

    @property
    def subgroup_default(self) -> Hashable | Literal[dataclasses.MISSING] | None:
        if not self.is_subgroup:
            raise RuntimeError(f"Field {self.field} doesn't have subgroups! ")
        return self.field.metadata.get("subgroup_default")

    @property
    def type_arguments(self) -> tuple[type, ...] | None:
        return utils.get_type_arguments(self.type)

    @property
    def parent(self) -> DataclassWrapper:
        return self._parent

    @property
    def subparsers_dict(self) -> dict[str, type] | None:
        """The dict of subparsers, which is created either when using a Union[<dataclass_1>,

        <dataclass_2>] type annotation, or when using the `subparsers()` function.
        """
        if self.field.metadata.get("subparsers"):
            return self.field.metadata["subparsers"]
        elif self.is_union:
            type_arguments = utils.get_type_arguments(self.field.type)
            if type_arguments and any(map(utils.is_dataclass_type_or_typevar, type_arguments)):
                return {
                    utils.get_type_name(dataclass_type).lower(): dataclass_type
                    for dataclass_type in type_arguments
                }

    def add_subparsers(self, parser: ArgumentParser):
        assert self.is_subparser

        # add subparsers for each dataclass type in the field.
        default_value = self.field.default
        if default_value is dataclasses.MISSING:
            if self.field.default_factory is not dataclasses.MISSING:
                default_value = self.field.default_factory()

        add_subparser_kwargs = dict(
            title=self.name,
            description=self.help,
            dest=self.dest,
            parser_class=type(parser),
            required=(default_value is dataclasses.MISSING),
        )

        if sys.version_info[:2] == (3, 6):
            required = add_subparser_kwargs.pop("required")
            subparsers = parser.add_subparsers(**add_subparser_kwargs)
            subparsers.required = required
        else:
            subparsers = parser.add_subparsers(**add_subparser_kwargs)

        if default_value is not dataclasses.MISSING:
            parser.set_defaults(**{self.dest: default_value})
        # subparsers.required = default_value is dataclasses.MISSING
        for subcommand, dataclass_type in self.subparsers_dict.items():
            logger.debug(f"adding subparser '{subcommand}' for type {dataclass_type}")
            subparser = subparsers.add_parser(subcommand, formatter_class=parser.formatter_class)
            # Just for typing correctness, as we didn't explicitly change
            # the return type of subparsers.add_parser method.)
            subparser = cast("ArgumentParser", subparser)
            subparser.add_arguments(dataclass_type, dest=self.dest)

    def equivalent_argparse_code(self):
        arg_options = self.arg_options.copy()
        arg_options_string = f"{{'type': {arg_options.pop('type', str).__qualname__}"
        arg_options_string += str(arg_options).replace("{", ", ").replace(TEMPORARY_TOKEN, " ")
        return f"group.add_argument(*{self.option_strings}, **{arg_options_string})"


def only_keep_action_args(options: dict[str, Any], action: str | Any) -> dict[str, Any]:
    """Remove all the arguments in `options` that aren't required by the Action.

    Parameters
    ----------
    options : Dict[str, Any]
        A dictionary of options that would usually be passed to
        `add_arguments(*option_strings, **options)`.
    action : Union[str, Any]
        The action class or name.

    Returns
    -------
    Dict[str, Any]
        [description]
    """
    # TODO: explicitly test these custom actions?
    argparse_action_classes: dict[str, type[argparse.Action]] = {
        "store": argparse._StoreAction,
        "store_const": argparse._StoreConstAction,
        "store_true": argparse._StoreTrueAction,
        "store_false": argparse._StoreFalseAction,
        "append": argparse._AppendAction,
        "append_const": argparse._AppendConstAction,
        "count": argparse._CountAction,
        "help": argparse._HelpAction,
        "version": argparse._VersionAction,
        "parsers": argparse._SubParsersAction,
    }
    if action not in argparse_action_classes:
        # the provided `action` is not a standard argparse-action.
        # We don't remove any of the provided options.
        return options

    # Remove all the keys that aren't needed by the action constructor:
    action_class = argparse_action_classes[action]
    argspec = inspect.getfullargspec(action_class)

    if argspec.varargs is not None or argspec.varkw is not None:
        # if the constructor takes variable arguments, pass all the options.
        logger.debug("Constructor takes var args. returning all options.")
        return options

    args_to_keep = argspec.args + ["action"]

    kept_options, deleted_options = utils.keep_keys(options, args_to_keep)
    if deleted_options:
        logger.debug(
            f"Some auto-generated options were deleted, as they were "
            f"not required by the Action constructor: {deleted_options}."
        )
    if deleted_options:
        logger.debug(f"Kept options: \t{kept_options.keys()}")
        logger.debug(f"Removed options: \t{deleted_options.keys()}")
    return kept_options
