"""Utility functions that simplify defining field of dataclasses."""
from __future__ import annotations

import dataclasses
import functools
import inspect
import warnings
from collections import OrderedDict
from dataclasses import _MISSING_TYPE, MISSING
from enum import Enum
from logging import getLogger
from typing import Any, Callable, Hashable, Iterable, TypeVar, overload

from typing_extensions import Literal, ParamSpec

from simple_parsing.helpers.custom_actions import (
    DEFAULT_NEGATIVE_PREFIX,
    BooleanOptionalAction,
)
from simple_parsing.utils import DataclassT, str2bool

# NOTE: backward-compatibility import because it was moved to a different file.
from .subgroups import subgroups  # noqa: F401

logger = getLogger(__name__)

E = TypeVar("E", bound=Enum)
K = TypeVar("K", bound=Hashable)
V = TypeVar("V")
T = TypeVar("T")


def field(
    default: T | _MISSING_TYPE = MISSING,
    alias: str | list[str] | None = None,
    cmd: bool = True,
    positional: bool = False,
    *,
    to_dict: bool = True,
    encoding_fn: Callable[[T], Any] | None = None,
    decoding_fn: Callable[[Any], T] | None = None,
    # dataclasses.field arguments
    default_factory: Callable[[], T] | _MISSING_TYPE = MISSING,
    init: bool = True,
    repr: bool = True,
    hash: bool | None = None,
    compare: bool = True,
    metadata: dict[str, Any] | None = None,
    **custom_argparse_args: Any,
) -> T:
    """Extension of the `dataclasses.field` function.

    Adds the ability to customize how this field's command-line options are
    created, as well as how it is serialized / deseralized (if the containing
    dataclass inherits from `simple_parsing.Serializable`.

    Leftover arguments are fed directly to the
    `ArgumentParser.add_argument(*option_strings, **kwargs)` method.

    Parameters
    ----------
    default : Union[T, _MISSING_TYPE], optional
        The default field value (same as in `dataclasses.field`), by default MISSING
    alias : Union[str, List[str]], optional
        Additional option_strings to pass to the `add_argument` method, by
        default None. When passing strings which do not start by "-" or "--",
        will be prefixed with "-" if the string is one character and by "--"
        otherwise.
    cmd: bool, optional
        Whether to add command-line arguments for this field or not. Defaults to
        True.

    ## Serialization-related Keyword Arguments:

    to_dict : bool
        Whether to include this field in the dictionary when calling `to_dict()`.
        Defaults to True.
        Only has an effect when the dataclass containing this field is
        `Serializable`.
    encoding_fn : Callable[[T], Any], optional
        Function to apply to this field's value when encoding the dataclass to a
        dict. Only has an effect when the dataclass containing this field is
        `Serializable`.
    decoding_fn : Callable[[Any], T]. optional
        Function to use in order to recover a the value of this field from a
        serialized entry in a dictionary (inside `cls.from_dict`).
        Only has an effect when the dataclass containing this field is
        `Serializable`.

    ## Keyword Arguments of `dataclasses.field`

    default_factory : Union[Callable[[], T], _MISSING_TYPE], optional
        (same as in `dataclasses.field`), by default None
    init : bool, optional
        (same as in `dataclasses.field`), by default True
    repr : bool, optional
        (same as in `dataclasses.field`), by default True
    hash : bool, optional
        (same as in `dataclasses.field`), by default None
    compare : bool, optional
        (same as in `dataclasses.field`), by default True
    metadata : Dict[str, Any], optional
        (same as in `dataclasses.field`), by default None

    Returns
    -------
    T
        The value returned by the `dataclasses.field` function.
    """
    _metadata: dict[str, Any] = metadata if metadata is not None else {}
    if alias:
        _metadata["alias"] = alias if isinstance(alias, list) else [alias]
    _metadata.update(dict(to_dict=to_dict))
    if encoding_fn is not None:
        _metadata.update(dict(encoding_fn=encoding_fn))
    if decoding_fn is not None:
        _metadata.update(dict(decoding_fn=decoding_fn))
    _metadata["cmd"] = cmd
    _metadata["positional"] = positional

    if custom_argparse_args:
        _metadata.update({"custom_args": custom_argparse_args})

        action = custom_argparse_args.get("action")
        if action == "store_false":
            if default not in {MISSING, True}:
                raise RuntimeError(
                    "default should either not be passed or set "
                    "to True when using the store_false action."
                )
            default = True  # type: ignore
        elif action == "store_true":
            if default not in {MISSING, False}:
                raise RuntimeError(
                    "default should either not be passed or set "
                    "to False when using the store_true action."
                )
            default = False  # type: ignore
    if default is not MISSING:
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


@overload
def choice(
    choices: type[E],
    *,
    default: E,
    default_factory: Callable[[], E] | _MISSING_TYPE = MISSING,
    **kwargs,
) -> E:
    ...


@overload
def choice(choices: dict[K, V], *, default: K, **kwargs) -> V:
    ...


@overload
def choice(
    *choices: T,
    default: T | _MISSING_TYPE = MISSING,
    default_factory: Callable[[], T] | _MISSING_TYPE = MISSING,
    **kwargs,
) -> T:
    ...


def choice(*choices, default=MISSING, **kwargs):
    """Makes a field which can be chosen from the set of choices from the command-line.

    Returns a regular `dataclasses.field()`, but with metadata which indicates
    the allowed values.

    (New:) If `choices` is a dictionary, then passing the 'key' will result in
    the corresponding value being used. The values may be objects, for example.
    Similarly for Enum types, passing a type of enum will

    Args:
        default (T, optional): The default value of the field. Defaults to dataclasses.MISSING,
        in which case the command-line argument is required.

    Raises:
        ValueError: If the default value isn't part of the given choices.

    Returns:
        T: the result of the usual `dataclasses.field()` function (a dataclass field/attribute).
    """
    assert len(choices) > 0, "Choice requires at least one positional argument!"

    if len(choices) == 1:
        choices = choices[0]
        if inspect.isclass(choices) and issubclass(choices, Enum):
            # If given an enum, construct a mapping from names to values.
            choice_enum: type[Enum] = choices
            choices = OrderedDict((e.name, e) for e in choice_enum)
            if default is not MISSING and not isinstance(default, choice_enum):
                if default in choices:
                    warnings.warn(
                        UserWarning(
                            f"Setting default={default} could perhaps be ambiguous "
                            f"(enum names vs enum values). Consider using the enum "
                            f"value {choices[default]} instead."
                        )
                    )
                    default = choices[default]
                else:
                    raise ValueError(
                        f"'default' arg should be of type {choice_enum}, but got {default}"
                    )

        if isinstance(choices, dict):
            # if the choices is a dict, the options are the keys
            # save the info about the choice_dict in the field metadata.
            metadata = kwargs.setdefault("metadata", {})
            choice_dict = choices
            # save the choice_dict in metadata so that we can recover the values in postprocessing.
            metadata["choice_dict"] = choice_dict
            choices = list(choice_dict.keys())

            # TODO: If the choice dict is given, then add encoding/decoding functions that just
            # get/set the right key.
            def _encoding_fn(value: Any) -> str:
                """Custom encoding function that will simply represent the value as the the key in
                the dict rather than the value itself."""
                if value in choice_dict.keys():
                    return value
                elif value in choice_dict.values():
                    return [k for k, v in choice_dict.items() if v == value][0]
                return value

            kwargs.setdefault("encoding_fn", _encoding_fn)

            def _decoding_fn(value: Any) -> Any:
                """Custom decoding function that will retrieve the value from the stored key in the
                dictionary."""
                return choice_dict.get(value, value)

            kwargs.setdefault("decoding_fn", _decoding_fn)

    return field(default=default, choices=choices, **kwargs)


def list_field(*default_items: T, **kwargs) -> list[T]:
    """shorthand function for setting a `list` attribute on a dataclass, so that every instance of
    the dataclass doesn't share the same list.

    Accepts any of the arguments of the `dataclasses.field` function.

    Returns:
        List[T]: a `dataclasses.field` of type `list`, containing the `default_items`.
    """
    if "default" in kwargs and isinstance(kwargs["default"], list):
        assert not default_items
        # can't have that. field wants a default_factory.
        # we just give back a copy of the list as a default factory,
        # but this should be discouraged.
        from copy import deepcopy

        default_factory = functools.partial(deepcopy, kwargs.pop("default"))
    else:
        default_factory = functools.partial(list, default_items)

    return field(default_factory=default_factory, **kwargs)


def dict_field(default_items: dict[K, V] | Iterable[tuple[K, V]] = (), **kwargs) -> dict[K, V]:
    """shorthand function for setting a `dict` attribute on a dataclass, so that every instance of
    the dataclass doesn't share the same `dict`.

    NOTE: Do not use keyword arguments as you usually would with a dictionary
    (as in something like `dict_field(a=1, b=2, c=3)`). Instead pass in a
    dictionary instance with the items: `dict_field(dict(a=1, b=2, c=3))`.
    The reason for this is that the keyword arguments are interpreted as custom
    argparse arguments, rather than arguments of the `dict` function!)

    Also accepts any of the arguments of the `dataclasses.field` function.

    Returns:
        Dict[K, V]: a `dataclasses.Field` of type `Dict[K, V]`, containing the `default_items`.
    """
    return field(default_factory=functools.partial(dict, default_items), **kwargs)


def set_field(*default_items: T, **kwargs) -> set[T]:
    return field(default_factory=functools.partial(set, default_items), **kwargs)


P = ParamSpec("P")


def mutable_field(
    fn: Callable[P, T],
    init: bool = True,
    repr: bool = True,
    hash: bool | None = None,
    compare: bool = True,
    metadata: dict[str, Any] | None = None,
    *fn_args: P.args,
    **fn_kwargs: P.kwargs,
) -> T:
    """Shorthand for `dataclasses.field(default_factory=functools.partial(fn, *fn_args,

    **fn_kwargs))`.

    NOTE: The *fn_args and **fn_kwargs here are passed to `fn`, and are never used by the argparse
    Action!
    """
    # TODO: Use this 'smart' partial to make it easier to define nested fields.
    # from simple_parsing.helpers.nested_partial import npartial
    default_factory = functools.partial(fn, *fn_args, **fn_kwargs)
    return dataclasses.field(
        default_factory=default_factory,
        init=init,
        repr=repr,
        hash=hash,
        compare=compare,
        metadata=metadata,
    )


def subparsers(
    subcommands: dict[str, type[DataclassT]],
    default: DataclassT | _MISSING_TYPE = MISSING,
    **kwargs,
) -> Any:
    return field(
        metadata={
            "subparsers": subcommands,
        },
        default=default,
        **kwargs,
    )


@overload
def flag(
    default: _MISSING_TYPE = MISSING,
    *,
    default_factory: _MISSING_TYPE = MISSING,
    negative_prefix: str | None = DEFAULT_NEGATIVE_PREFIX,
    negative_option: str | None = None,
    nargs: Literal["?"] | None = None,
    type: Callable[[str], bool] = str2bool,
    action: type[BooleanOptionalAction] = BooleanOptionalAction,
    **kwargs,
) -> bool:
    ...


@overload
def flag(
    default: bool,
    *,
    default_factory: _MISSING_TYPE = MISSING,
    negative_prefix: str | None = DEFAULT_NEGATIVE_PREFIX,
    negative_option: str | None = None,
    nargs: Literal["?"] | None = None,
    type: Callable[[str], bool] = str2bool,
    action: type[BooleanOptionalAction] = BooleanOptionalAction,
    **kwargs,
) -> bool:
    ...


@overload
def flag(
    default: _MISSING_TYPE = MISSING,
    *,
    default_factory: Callable[[], bool] = ...,
    negative_prefix: str | None = DEFAULT_NEGATIVE_PREFIX,
    negative_option: str | None = None,
    nargs: Literal["?"] | None = None,
    type: Callable[[str], bool] = str2bool,
    action: type[BooleanOptionalAction] = BooleanOptionalAction,
    **kwargs,
) -> bool:
    ...


def flag(
    default: bool | _MISSING_TYPE = MISSING,
    *,
    default_factory: Callable[[], bool] | _MISSING_TYPE = MISSING,
    negative_prefix: str | None = DEFAULT_NEGATIVE_PREFIX,
    negative_option: str | None = None,
    nargs: Literal["?"] | None = None,
    type: Callable[[str], bool] = str2bool,
    action: type[BooleanOptionalAction] = BooleanOptionalAction,
    **kwargs,
) -> bool:
    """A boolean field with a positive and negative command-line argument.

    If either `default` or `default_factory` are set, then both the field and the generated
    command-line arguments are optional. Otherwise, both are required.

    Negative flags are generated using `negative_prefix` and `negative_option`:
    - When `negative_option` is passed, it is used to create the negative flag.
    - Otherwise, `negative_prefix` is prepended to the field name to create the negative flag.

    NOTE: The negative flags don't accept a value. (i.e. `--noverbose` works, but
    `--noverbose=True` does not.)
    The positive flags can be used either with or without a value.
    """
    return field(
        default=default,
        default_factory=default_factory,
        negative_prefix=negative_prefix,
        negative_option=negative_option,
        nargs=nargs,
        type=type,
        action=action,
        **kwargs,
    )


def flags(
    default_factory: Callable[[], list[bool]] | _MISSING_TYPE = MISSING,
    nargs: Literal["*", "+"] | int = "*",
    type: Callable[[str], bool] = str2bool,
    **kwargs,
) -> list[bool]:
    return field(
        default_factory=default_factory,
        nargs=nargs,
        type=type,
        **kwargs,
    )
