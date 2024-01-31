"""Functions for decoding dataclass fields from "raw" values (e.g. from json)."""
from __future__ import annotations

import inspect
import sys
import warnings
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import Field
from enum import Enum
from functools import partial
from logging import getLogger
from pathlib import Path
from typing import Any, Callable, TypeVar

from simple_parsing.annotation_utils.get_field_annotations import (
    evaluate_string_annotation,
)
from simple_parsing.utils import (
    get_bound,
    get_forward_arg,
    get_type_arguments,
    is_dataclass_type,
    is_dict,
    is_enum,
    is_forward_ref,
    is_list,
    is_literal,
    is_set,
    is_tuple,
    is_typevar,
    is_union,
    str2bool,
)

logger = getLogger(__name__)

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

# Dictionary mapping from types/type annotations to their decoding functions.
_decoding_fns: dict[type[T], Callable[[Any], T]] = {
    # the 'primitive' types are decoded using the type fn as a constructor.
    t: t
    for t in [str, bytes]
}


def register_decoding_fn(
    some_type: type[T], function: Callable[[Any], T], overwrite: bool = False
) -> None:
    """Register a decoding function for the type `some_type`."""
    _register(some_type, function, overwrite=overwrite)


def _register(t: type, func: Callable, overwrite: bool = False) -> None:
    if t not in _decoding_fns or overwrite:
        # logger.debug(f"Registering the type {t} with decoding function {func}")
        _decoding_fns[t] = func


C = TypeVar("C", bound=Callable[[Any], Any])


def decoding_fn_for_type(some_type: type) -> Callable[[C], C]:
    """Registers a function to be used to convert a serialized value to the given type.

    The function should accept one argument (the serialized value) and return the decoded value.
    """

    def _wrapper(fn: C) -> C:
        register_decoding_fn(some_type, fn, overwrite=True)
        return fn

    return _wrapper


@decoding_fn_for_type(int)
def _decode_int(v: str) -> int:
    int_v = int(v)
    if isinstance(v, bool):
        warnings.warn(UnsafeCastingWarning(raw_value=v, decoded_value=int_v))
    elif int_v != float(v):
        warnings.warn(UnsafeCastingWarning(raw_value=v, decoded_value=int_v))
    return int_v


@decoding_fn_for_type(float)
def _decode_float(v: Any) -> float:
    float_v = float(v)
    if isinstance(v, bool):
        warnings.warn(UnsafeCastingWarning(raw_value=v, decoded_value=float_v))
    return float_v


@decoding_fn_for_type(bool)
def _decode_bool(v: Any) -> bool:
    if isinstance(v, str):
        bool_v = str2bool(v)
    else:
        bool_v = bool(v)
        if isinstance(v, (int, float)) and v not in (0, 1, 0.0, 1.0):
            warnings.warn(UnsafeCastingWarning(raw_value=v, decoded_value=bool_v))
    return bool_v


def decode_field(
    field: Field,
    raw_value: Any,
    containing_dataclass: type | None = None,
    drop_extra_fields: bool | None = None,
) -> Any:
    """Converts a "raw" value (e.g. from json file) to the type of the `field`.

    When serializing a dataclass to json, all objects are converted to dicts.
    The values which have a special type (not str, int, float, bool) are
    converted to string or dict. Hence this function allows us to recover the
    original type of pretty much any field which is of type `Serializable`, or
    has a registered decoding function (either through `register_decoding_fn` or
    through having `decoding_fn` passed directly to the `field` function.

    Args:
        field (Field): `Field` object from a dataclass.
        raw_value (Any): The `raw` value from deserializing the dataclass.

    Returns:
        Any: The "raw" value converted to the right type.
    """
    name = field.name
    field_type = field.type
    logger.debug(f"name = {name}, field_type = {field_type}")

    # If the user set a custom decoding function, we use it.
    custom_decoding_fn = field.metadata.get("decoding_fn")
    if custom_decoding_fn is not None:
        return custom_decoding_fn(raw_value)

    if isinstance(field_type, str) and containing_dataclass:
        field_type = evaluate_string_annotation(field_type, containing_dataclass)

    decoding_function = get_decoding_fn(field_type)

    _kwargs = dict(category=UnsafeCastingWarning) if sys.version_info >= (3, 11) else {}

    with warnings.catch_warnings(record=True, **_kwargs) as warning_messages:
        if is_dataclass_type(field_type) and drop_extra_fields is not None:
            # Pass the drop_extra_fields argument to the decoding function.
            decoded_value = decoding_function(raw_value, drop_extra_fields=drop_extra_fields)
        else:
            decoded_value = decoding_function(raw_value)

    for warning_message in warning_messages.copy():
        if not isinstance(warning_message.message, UnsafeCastingWarning):
            warnings.warn_explicit(
                message=warning_message.message,
                category=warning_message.category,
                filename=warning_message.filename,
                lineno=warning_message.lineno,
                # module=warning_message.module,
                # registry=warning_message.registry,
                # module_globals=warning_message.module_globals,
            )
            warning_messages.remove(warning_message)

    if warning_messages:
        warnings.warn(
            RuntimeWarning(
                f"Unsafe casting occurred when deserializing field '{name}' of type {field_type}: "
                f"raw value: {raw_value!r}, decoded value: {decoded_value!r}."
            )
        )
    return decoded_value


# NOTE: Disabling the caching here might help avoid some bugs, and it's unclear if this has that
# much of a performance impact.
def get_decoding_fn(type_annotation: type[T] | str) -> Callable[..., T]:
    """Fetches/Creates a decoding function for the given type annotation.

    This decoding function can then be used to create an instance of the type
    when deserializing dicts (which could have been obtained with JSON or YAML).

    This function inspects the type annotation and creates the right decoding
    function recursively in a "dynamic-programming-ish" fashion.
    NOTE: We cache the results in a `functools.lru_cache` decorator to avoid
    wasteful calls to the function. This makes this process pretty efficient.

    Args:
        t (Type[T]):
            A type or type annotation. Can be arbitrarily nested.
            For example:
            - List[int]
            - Dict[str, Foo]
            - Tuple[int, str, Any],
            - Dict[Tuple[int, int], List[str]]
            - List[List[List[List[Tuple[int, str]]]]]
            - etc.

    Returns:
        Callable[[Any], T]:
            A function that decodes a 'raw' value to an instance of type `t`.
    """
    from .serializable import from_dict

    logger.debug(f"Getting the decoding function for {type_annotation!r}")

    if isinstance(type_annotation, str):
        # Check first if there are any matching registered decoding functions.
        # TODO: Might be better to actually use the scope of the field, right?
        matching_entries = {
            key: decoding_fn
            for key, decoding_fn in _decoding_fns.items()
            if (inspect.isclass(key) and key.__name__ == type_annotation)
        }
        if len(matching_entries) == 1:
            _, decoding_fn = matching_entries.popitem()
            return decoding_fn
        elif len(matching_entries) > 1:
            # Multiple decoding functions match the type. Can't tell.
            logger.warning(
                RuntimeWarning(
                    f"More than one potential decoding functions were found for types that match "
                    f"the string annotation {type_annotation!r}. This will simply try each one "
                    f"and return the first one that works."
                )
            )
            return try_functions(*(decoding_fn for _, decoding_fn in matching_entries.items()))
        else:
            # Try to evaluate the string annotation.
            t = evaluate_string_annotation(type_annotation)

    elif is_forward_ref(type_annotation):
        forward_arg: str = get_forward_arg(type_annotation)
        # Recurse until we've resolved the forward reference.
        return get_decoding_fn(forward_arg)

    else:
        t = type_annotation

    logger.debug(f"{type_annotation!r} -> {t!r}")

    # T should now be a type or one of the objects from the typing module.

    if t in _decoding_fns:
        # The type has a dedicated decoding function.
        return _decoding_fns[t]

    if is_dataclass_type(t):
        return partial(from_dict, t)

    if t is Any:
        logger.debug(f"Decoding an Any type: {t}")
        return no_op

    if is_dict(t):
        logger.debug(f"Decoding a Dict field: {t}")
        args = get_type_arguments(t)
        if len(args) != 2:
            args = (Any, Any)
        return decode_dict(*args)

    if is_set(t):
        logger.debug(f"Decoding a Set field: {t}")
        args = get_type_arguments(t)
        if len(args) != 1:
            args = (Any,)
        return decode_set(args[0])

    if is_tuple(t):
        logger.debug(f"Decoding a Tuple field: {t}")
        args = get_type_arguments(t)
        return decode_tuple(*args)

    if is_list(t):
        logger.debug(f"Decoding a List field: {t}")
        args = get_type_arguments(t)
        if not args:
            # Using a `List` or `list` annotation, so we don't know what do decode the
            # items into!
            args = (Any,)
        assert len(args) == 1
        return decode_list(args[0])

    if is_union(t):
        logger.debug(f"Decoding a Union field: {t}")
        args = get_type_arguments(t)
        return decode_union(*args)

    if is_enum(t):
        logger.debug(f"Decoding an Enum field: {t}")
        return decode_enum(t)

    if is_typevar(t):
        bound = get_bound(t)
        logger.debug(f"Decoding a typevar: {t}, bound type is {bound}.")
        if bound is not None:
            return get_decoding_fn(bound)

    if is_literal(t):
        logger.debug(f"Decoding a Literal field: {t}")
        possible_vals = get_type_arguments(t)
        return decode_literal(*possible_vals)

    # Unknown type.
    warnings.warn(
        UserWarning(
            f"Unable to find a decoding function for the annotation {t} (of type {type(t)}). "
            f"Will try to use the type as a constructor. Consider registering a decoding function "
            f"using `register_decoding_fn`, or posting an issue on GitHub. "
        )
    )
    return try_constructor(t)


def decode_optional(t: type[T]) -> Callable[[Any | None], T | None]:
    decode = get_decoding_fn(t)

    def _decode_optional(val: Any | None) -> T | None:
        return val if val is None else decode(val)

    return _decode_optional


def try_functions(*funcs: Callable[[Any], T]) -> Callable[[Any], T | Any]:
    """Tries to use the functions in succession, else returns the same value unchanged."""

    def _try_functions(val: Any) -> T | Any:
        e: Exception | None = None
        for func in funcs:
            try:
                return func(val)
            except Exception as ex:
                e = ex
        else:
            logger.debug(f"Couldn't parse value {val}, returning it as-is. (exception: {e})")
        return val

    return _try_functions


def decode_union(*types: type[T]) -> Callable[[Any], T | Any]:
    types_list = list(types)
    optional = type(None) in types_list

    # Partition the Union into None and non-None types.
    while type(None) in types_list:
        types_list.remove(type(None))

    decoding_fns: list[Callable[[Any], T]] = [
        decode_optional(t) if optional else get_decoding_fn(t) for t in types_list
    ]

    # TODO: We could be a bit smarter about the order in which we try the functions, but for now,
    # we just try the functions in the same order as the annotation, and return the result from the
    # first function that doesn't raise an exception.

    # Try using each of the non-None types, in succession. Worst case, return the value.
    return try_functions(*decoding_fns)


def decode_list(t: type[T]) -> Callable[[list[Any]], list[T]]:
    decode_item = get_decoding_fn(t)

    def _decode_list(val: list[Any]) -> list[T]:
        return [decode_item(v) for v in val]

    return _decode_list


def decode_tuple(*tuple_item_types: type[T]) -> Callable[[list[T]], tuple[T, ...]]:
    """Makes a parsing function for creating tuples.

    Can handle tuples with different item types, for instance:
    - `Tuple[int, Foo, str, float, ...]`.

    Returns:
        Callable[[List[T]], Tuple[T, ...]]: A parsing function for creating tuples.
    """
    # Get the decoding function for each item type
    has_ellipsis = False
    if Ellipsis in tuple_item_types:
        # TODO: This isn't necessary, the ellipsis will always be at index 1.
        ellipsis_index = tuple_item_types.index(Ellipsis)
        decoding_fn_index = ellipsis_index - 1
        decoding_fn = get_decoding_fn(tuple_item_types[decoding_fn_index])
        has_ellipsis = True
    else:
        decoding_fns = [get_decoding_fn(t) for t in tuple_item_types]
    # Note, if there are more values than types in the tuple type, then the
    # last type is used.

    def _decode_tuple(val: tuple[Any, ...]) -> tuple[T, ...]:
        if has_ellipsis:
            return tuple(decoding_fn(v) for v in val)
        else:
            return tuple(decoding_fns[i](v) for i, v in enumerate(val))

    return _decode_tuple


def decode_set(item_type: type[T]) -> Callable[[list[T]], set[T]]:
    """Makes a parsing function for creating sets with items of type `item_type`.

    Args:
        item_type (Type[T]): the type of the items in the set.

    Returns:
        Callable[[List[T]], Set[T]]: [description]
    """
    # Get the parse fn for a list of items of type `item_type`.
    parse_list_fn = decode_list(item_type)

    def _decode_set(val: list[Any]) -> set[T]:
        return set(parse_list_fn(val))

    return _decode_set


def decode_dict(K_: type[K], V_: type[V]) -> Callable[[list[tuple[Any, Any]]], dict[K, V]]:
    """Creates a decoding function for a dict type. Works with OrderedDict too.

    Args:
        K_ (Type[K]): The type of the keys.
        V_ (Type[V]): The type of the values.

    Returns:
        Callable[[List[Tuple[Any, Any]]], Dict[K, V]]: A function that parses a
            Dict[K_, V_].
    """
    decode_k = get_decoding_fn(K_)
    decode_v = get_decoding_fn(V_)

    def _decode_dict(val: dict[Any, Any] | list[tuple[Any, Any]]) -> dict[K, V]:
        result: dict[K, V] = {}
        if isinstance(val, list):
            result = OrderedDict()
            items = val
        elif isinstance(val, OrderedDict):
            # NOTE(ycho): Needed to propagate `OrderedDict` type
            result = OrderedDict()
            items = val.items()
        else:
            items = val.items()
        for k, v in items:
            k_ = decode_k(k)
            v_ = decode_v(v)
            result[k_] = v_
        return result

    return _decode_dict


def decode_enum(item_type: type[Enum]) -> Callable[[str], Enum]:
    """Creates a decoding function for an enum type.

    Args:
        item_type (Type[Enum]): the type of the items in the set.

    Returns:
        Callable[[str], Enum]: A function that returns the enum member for the given name.
    """

    def _decode_enum(val: str) -> Enum:
        return item_type[val]

    return _decode_enum


def decode_literal(*possible_vals: Any) -> Callable[[Any], Any]:
    """Creates a decoding function for a Literal type.

    Args:
        *possible_vals (Any): The permissible values for the Literal type.

    Returns:
        Callable[[Any], Any]: A function that checks if a given value is one of the
            permissible values for the Literal. If not, raises a TypeError.
    """

    def _decode_literal(val: Any) -> Any:
        if val not in possible_vals:
            raise TypeError(f"Expected one of {possible_vals} for Literal, got {val}")

        return val

    return _decode_literal


def no_op(v: T) -> T:
    """Decoding function that gives back the value as-is.

    Args:
        v ([Any]): Any value.

    Returns:
        [type]: The value unchanged.
    """
    return v


def try_constructor(t: type[T]) -> Callable[[Any], T | Any]:
    """Tries to use the type as a constructor. If that fails, returns the value as-is.

    Args:
        t (Type[T]): A type.

    Returns:
        Callable[[Any], Union[T, Any]]: A decoding function that might return nothing.
    """

    def constructor(val):
        if isinstance(val, Mapping):
            return t(**val)
        else:
            return t(val)

    return try_functions(constructor)


register_decoding_fn(Path, Path)


class UnsafeCastingWarning(RuntimeWarning):
    def __init__(self, raw_value: Any, decoded_value: Any) -> None:
        super().__init__()
        self.raw_value = raw_value
        self.decoded_value = decoded_value
