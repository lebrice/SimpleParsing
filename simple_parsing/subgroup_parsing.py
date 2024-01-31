from __future__ import annotations

import argparse
import dataclasses
import functools
import itertools
import typing
import warnings
from argparse import Namespace
from logging import getLogger as get_logger
from typing import Any, Callable, Hashable

from simple_parsing.helpers.serialization.serializable import DC_TYPE_KEY
from simple_parsing.helpers.subgroups import SubgroupKey
from simple_parsing.replace import SUBGROUP_KEY_FLAG
from simple_parsing.utils import (
    Dataclass,
    PossiblyNestedDict,
    is_dataclass_instance,
    is_dataclass_type,
)
from simple_parsing.wrappers import DataclassWrapper, FieldWrapper

if typing.TYPE_CHECKING:
    from simple_parsing.parsing import ArgumentParser


logger = get_logger(__name__)


def resolve_subgroups(
    parser: ArgumentParser,
    wrappers: list[DataclassWrapper],
    args: list[str],
    namespace: Namespace | None = None,
) -> tuple[list[DataclassWrapper], dict[str, str]]:
    """Iteratively add and resolve all the choice of argument subgroups, if any.

    This modifies the wrappers in-place, by possibly adding children to the wrappers in the
    list.
    Returns a list with the (now modified) wrappers.

    Each round does the following:
    1.  Resolve any conflicts using the conflict resolver. Two subgroups at the same nesting
        level, with the same name, get a different prefix, for example "--generator.optimizer"
        and "--discriminator.optimizer".
    2.  Add all the subgroup choice arguments to a parser.
    3.  Add the chosen dataclasses to the list of dataclasses to parse later in the main
        parser. This is done by adding wrapping the dataclass and adding it to the `wrappers`
        list.
    """

    unresolved_subgroups = _get_subgroup_fields(wrappers)
    # Dictionary of the subgroup choices that were resolved (key: subgroup dest, value: chosen
    # subgroup name).
    resolved_subgroups: dict[str, SubgroupKey] = {}

    if not unresolved_subgroups:
        # No subgroups to parse.
        return wrappers, {}

    # Use a temporary parser, to avoid parsing "vanilla argparse" arguments of `self` multiple
    # times.
    subgroup_choice_parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=parser.formatter_class,
        # NOTE: We disallow abbreviations for subgroups for now. This prevents potential issues
        # for example if you have —a_or_b and A has a field —a then it will error out if you
        # pass —a=1 because 1 isn’t a choice for the a_or_b argument (because --a matches it
        # with the abbreviation feature turned on).
        allow_abbrev=False,
    )

    for current_nesting_level in itertools.count():
        # Do rounds of parsing with just the subgroup arguments, until all the subgroups
        # are resolved to a dataclass type.
        logger.debug(
            f"Starting subgroup parsing round {current_nesting_level}: "
            f"{list(unresolved_subgroups.keys())}"
        )
        # Add all the unresolved subgroups arguments.
        for dest, subgroup_field in unresolved_subgroups.items():
            flags = subgroup_field.option_strings
            argument_options = subgroup_field.arg_options

            # Sanity checks:
            if subgroup_field.subgroup_default is dataclasses.MISSING:
                assert argument_options["required"]
                if "default" in argument_options:
                    # todo: should ideally not set this in the first place...
                    assert argument_options["default"] is dataclasses.MISSING
                    argument_options.pop("default")
                assert "default" not in argument_options
            else:
                assert "default" in argument_options
                assert argument_options["default"] == subgroup_field.default
                argument_options["default"] = _adjust_default_value_for_subgroup_field(
                    subgroup_field=subgroup_field,
                    subgroup_default=argument_options["default"],
                )

            logger.debug(
                f"Adding subgroup argument: add_argument(*{flags} **{str(argument_options)})"
            )
            subgroup_choice_parser.add_argument(*flags, **argument_options)

        # Parse `args` repeatedly until all the subgroup choices are resolved.
        parsed_args, unused_args = subgroup_choice_parser.parse_known_args(
            args=args, namespace=namespace
        )
        logger.debug(
            f"Nesting level {current_nesting_level}: args: {args}, "
            f"parsed_args: {parsed_args}, unused_args: {unused_args}"
        )

        for dest, subgroup_field in list(unresolved_subgroups.items()):
            # NOTE: There should always be a parsed value for the subgroup argument on the
            # namespace. This is because we added all the subgroup arguments before we get
            # here.
            subgroup_dict = subgroup_field.subgroup_choices
            chosen_subgroup_key: SubgroupKey = getattr(parsed_args, dest)
            assert chosen_subgroup_key in subgroup_dict

            # Changing the default value of the (now parsed) field for the subgroup choice,
            # just so it shows (default: {chosen_subgroup_key}) on the command-line.
            # Note: This really isn't required, we could have it just be the default value, but
            # it seems a bit more consistent with us then showing the --help string for the
            # chosen dataclass type (as we're doing below).
            # subgroup_field.set_default(chosen_subgroup_key)
            logger.debug(
                f"resolved the subgroup at {dest!r}: will use the subgroup at key "
                f"{chosen_subgroup_key!r}"
            )

            default_or_dataclass_fn = subgroup_dict[chosen_subgroup_key]
            if is_dataclass_instance(default_or_dataclass_fn):
                # The chosen value in the subgroup dict is a frozen dataclass instance.
                default = default_or_dataclass_fn
                dataclass_fn = functools.partial(dataclasses.replace, default)
                dataclass_type = type(default)
            else:
                default = None
                dataclass_fn = default_or_dataclass_fn
                dataclass_type = subgroup_field.field.metadata["subgroup_dataclass_types"][
                    chosen_subgroup_key
                ]

            assert default is None or is_dataclass_instance(default)
            assert callable(dataclass_fn)
            assert is_dataclass_type(dataclass_type)

            name = dest.split(".")[-1]
            parent_dataclass_wrapper = subgroup_field.parent
            # NOTE: Using self._add_arguments so it returns the modified wrapper and doesn't
            # affect the `self._wrappers` list.
            new_wrapper = parser._add_arguments(
                dataclass_type=dataclass_type,
                name=name,
                dataclass_fn=dataclass_fn,
                default=default,
                parent=parent_dataclass_wrapper,
            )
            # Make the new wrapper a child of the class which contains the field.
            # - it isn't already a child
            # - it's parent is the parent dataclass wrapper
            # - the parent is already in the tree of DataclassWrappers.
            assert new_wrapper not in parent_dataclass_wrapper._children
            parent_dataclass_wrapper._children.append(new_wrapper)
            assert new_wrapper.parent is parent_dataclass_wrapper
            assert parent_dataclass_wrapper in _flatten_wrappers(wrappers)
            assert new_wrapper in _flatten_wrappers(wrappers)

            # Mark this subgroup as resolved.
            unresolved_subgroups.pop(dest)
            resolved_subgroups[dest] = chosen_subgroup_key
            # TODO: Should we remove the FieldWrapper for the subgroups now that it's been
            # resolved?

        # Find the new subgroup fields that weren't resolved before.
        # TODO: What if a name conflict occurs between a subgroup field and one of the new
        # fields below it? For example, something like --model model_a (and inside the `ModelA`
        # dataclass, there's a field called `model`. Then, this will cause a conflict!)
        # For now, I'm just going to wait and see how this plays out. I'm hoping that the
        # auto conflict resolution shouldn't run into any issues in this case.

        wrappers = parser._conflict_resolver.resolve(wrappers)

        all_subgroup_fields = _get_subgroup_fields(wrappers)
        unresolved_subgroups = {
            k: v for k, v in all_subgroup_fields.items() if k not in resolved_subgroups
        }
        logger.debug(f"All subgroups: {list(all_subgroup_fields.keys())}")
        logger.debug(f"Resolved subgroups: {resolved_subgroups}")
        logger.debug(f"Unresolved subgroups: {list(unresolved_subgroups.keys())}")

        if not unresolved_subgroups:
            logger.debug("Done parsing all the subgroups!")
            break
        else:
            logger.debug(
                f"Done parsing a round of subparsers at nesting level "
                f"{current_nesting_level}. Moving to the next round which has "
                f"{len(unresolved_subgroups)} unresolved subgroup choices."
            )
    return wrappers, resolved_subgroups


def _get_subgroup_fields(wrappers: list[DataclassWrapper]) -> dict[str, FieldWrapper]:
    subgroup_fields = {}
    all_wrappers = _flatten_wrappers(wrappers)
    for wrapper in all_wrappers:
        for field in wrapper.fields:
            if field.is_subgroup:
                assert field not in subgroup_fields.values()
                subgroup_fields[field.dest] = field
    return subgroup_fields


def _flatten_wrappers(wrappers: list[DataclassWrapper]) -> list[DataclassWrapper]:
    """Takes a list of nodes, returns a flattened list of all nodes in the tree."""
    _assert_no_duplicates(wrappers)
    roots_only = _unflatten_wrappers(wrappers)
    return sum(([w] + list(w.descendants) for w in roots_only), [])


def _assert_no_duplicates(wrappers: list[DataclassWrapper]) -> None:
    if len(wrappers) != len(set(wrappers)):
        raise RuntimeError(
            "Duplicate wrappers found! This is a potentially nasty bug on our "
            "part. Please make an issue at https://www.github.com/lebrice/SimpleParsing/issues "
        )


def _unflatten_wrappers(wrappers: list[DataclassWrapper]) -> list[DataclassWrapper]:
    """Given a list of nodes in one or more trees, returns only the root nodes.

    In our context, this is all the dataclass arg groups that were added with
    `parser.add_arguments`.
    """
    _assert_no_duplicates(wrappers)
    return [w for w in wrappers if w.parent is None]


def remove_subgroups_from_namespace(
    argument_parser: ArgumentParser, parsed_args: argparse.Namespace
) -> None:
    """Removes the subgroup choice results from the namespace.

    Modifies the namespace in-place.
    """
    # find all subgroup fields
    subgroup_fields = _get_subgroup_fields(argument_parser._wrappers)

    if not subgroup_fields:
        return
    # IDEA: Store the choices in a `subgroups` dict on the namespace.
    if not hasattr(parsed_args, "subgroups"):
        parsed_args.subgroups = {}

    for dest in subgroup_fields:
        chosen_value = getattr(parsed_args, dest)
        parsed_args.subgroups[dest] = chosen_value
        delattr(parsed_args, dest)


def _adjust_default_value_for_subgroup_field(
    subgroup_field: FieldWrapper, subgroup_default: Any
) -> str | Hashable:
    if argparse.SUPPRESS in subgroup_field.parent.defaults:
        assert subgroup_default is argparse.SUPPRESS
        assert isinstance(subgroup_default, str)
        return subgroup_default

    if isinstance(subgroup_default, dict):
        default_from_config_file = subgroup_default
        default_from_dataclass_field = subgroup_field.subgroup_default

        if SUBGROUP_KEY_FLAG in default_from_config_file:
            _default_subgroup = default_from_config_file[SUBGROUP_KEY_FLAG]
            logger.debug(f"Using subgroup key {_default_subgroup} as default (from config file)")
            return _default_subgroup

        if DC_TYPE_KEY in default_from_config_file:
            # The type of dataclass is specified in the config file.
            # We can use that to figure out which subgroup to use.
            default_dataclass_type_from_config = default_from_config_file[DC_TYPE_KEY]
            if isinstance(default_dataclass_type_from_config, str):
                from simple_parsing.helpers.serialization.serializable import _locate

                # Try to import the type of dataclass given its import path as a string in the
                # config file.
                default_dataclass_type_from_config = _locate(default_dataclass_type_from_config)
            assert is_dataclass_type(default_dataclass_type_from_config)

            from simple_parsing.helpers.subgroups import _get_dataclass_type_from_callable

            subgroup_choices_with_matching_type: dict[
                Hashable, Dataclass | Callable[[], Dataclass]
            ] = {
                subgroup_key: subgroup_value
                for subgroup_key, subgroup_value in subgroup_field.subgroup_choices.items()
                if is_dataclass_type(subgroup_value)
                and subgroup_value == default_dataclass_type_from_config
                or is_dataclass_instance(subgroup_value)
                and type(subgroup_value) == default_dataclass_type_from_config
                or _get_dataclass_type_from_callable(subgroup_value)
                == default_dataclass_type_from_config
            }
            logger.debug(
                f"Subgroup choices that match the type in the config file: "
                f"{subgroup_choices_with_matching_type}"
            )
            if len(subgroup_choices_with_matching_type) > 1:
                raise RuntimeError(
                    f"The dataclass type {default_dataclass_type_from_config} matches more than "
                    f"one value in the subgroups dict:\n"
                    f"{subgroup_field.subgroup_choices}\n"
                    f"Use the {SUBGROUP_KEY_FLAG!r} flag to specify which subgroup key to use as "
                    f"the default."
                )
            return subgroup_choices_with_matching_type.popitem()[0]

            # IDEA: Try to find the best subgroup key to use, based on the number of matching
            # constructor arguments between the default in the config and the defaults for each
            # subgroup.
            constructor_args_of_each_subgroup_val = {
                key: (
                    dataclasses.asdict(subgroup_value)
                    if is_dataclass_instance(subgroup_value)
                    # (the type should have been narrowed by the is_dataclass_instance typeguard,
                    # but somehow isn't...)
                    else _default_constructor_argument_values(subgroup_value)  # type: ignore
                )
                for key, subgroup_value in subgroup_choices_with_matching_type.items()
            }
            logger.debug(
                f"Constructor arguments for each subgroup choice: "
                f"{constructor_args_of_each_subgroup_val}"
            )

            def _num_overlapping_keys(
                subgroup_default_in_config: PossiblyNestedDict[str, Any],
                subgroup_option_from_field: PossiblyNestedDict[str, Any],
            ) -> int:
                """Returns the number of matching entries in the subgroup dict w/ the default from
                the config."""
                overlap = 0
                for key, value in subgroup_default_in_config.items():
                    if key in subgroup_option_from_field:
                        overlap += 1
                        if isinstance(value, dict) and isinstance(
                            subgroup_option_from_field[key], dict
                        ):
                            overlap += _num_overlapping_keys(
                                value, subgroup_option_from_field[key]
                            )
                return overlap

            n_matching_values = {
                k: _num_overlapping_keys(default_from_config_file, constructor_args_in_value)
                for k, constructor_args_in_value in constructor_args_of_each_subgroup_val.items()
            }
            logger.debug(
                f"Number of overlapping keys for each subgroup choice: {n_matching_values}"
            )
            closest_subgroups_first = sorted(
                subgroup_choices_with_matching_type.keys(),
                key=n_matching_values.__getitem__,
                reverse=True,
            )
            closest_subgroup_key = closest_subgroups_first[0]

            warnings.warn(
                RuntimeWarning(
                    f"The config file contains a default value for a subgroup field that isn't in "
                    f"the dict of subgroup options. "
                    f"Because of how subgroups are currently implemented, we need to find the key "
                    f"in the subgroup choice dict that most closely matches the value "
                    f"{default_from_config_file} in order to populate the default values for "
                    f"other fields.\n"
                    f"The default in the config file: {default_from_config_file}\n"
                    f"The default in the dataclass field: {default_from_dataclass_field}\n"
                    f"The subgroups dict: {subgroup_field.subgroup_choices}\n"
                    f"The current implementation tries to use the dataclass type of this closest "
                    f"match to parse the additional values from the command-line. "
                    f"Consider adding a {SUBGROUP_KEY_FLAG!r}: <key of the subgroup to use> item "
                    f"in the dict entry for that subgroup field in your config, to make it easier "
                    f"to tell directly which subgroup to use."
                )
            )
            return closest_subgroup_key

        logger.debug(
            f"Using subgroup key {default_from_dataclass_field} as default (from the dataclass "
            f"field)"
        )
        return default_from_dataclass_field

    if subgroup_default in subgroup_field.subgroup_choices.keys():
        return subgroup_default

    if subgroup_default in subgroup_field.subgroup_choices.values():
        matching_keys = [
            k for k, v in subgroup_field.subgroup_choices.items() if v == subgroup_default
        ]
        return matching_keys[0]

    raise RuntimeError(
        f"Error: Unable to figure out what key matches the default value for the subgroup at "
        f"{subgroup_field.dest}! (expected to either have the {SUBGROUP_KEY_FLAG!r} flag set, or "
        f"one of the keys or values of the subgroups dict of that field: "
        f"{subgroup_field.subgroup_choices})"
    )
