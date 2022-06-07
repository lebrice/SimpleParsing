""" Functions for decoding dataclass fields from "raw" values (e.g. from json).
"""
import inspect
import warnings
from collections import OrderedDict
from collections.abc import Mapping
from dataclasses import Field
from enum import Enum
from functools import lru_cache, partial
from logging import getLogger
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, TypeVar, Union

from simple_parsing.annotation_utils.get_field_annotations import (
    evaluate_string_annotation,
)
from simple_parsing.utils import (
    get_bound,
    get_type_arguments,
    is_dict,
    is_enum,
    is_forward_ref,
    is_list,
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
_decoding_fns: Dict[Type[T], Callable[[Any], T]] = {
    # the 'primitive' types are decoded using the type fn as a constructor.
    t: t
    for t in [str, float, int, bytes]
}


def decode_bool(v: Any) -> bool:
    if isinstance(v, str):
        return str2bool(v)
    return bool(v)


_decoding_fns[bool] = decode_bool


def decode_field(field: Field, raw_value: Any, containing_dataclass: Optional[type] = None) -> Any:
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

    return get_decoding_fn(field_type)(raw_value)


@lru_cache(maxsize=100)
def get_decoding_fn(t: Type[T]) -> Callable[[Any], T]:
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
    # cache_info = get_decoding_fn.cache_info()
    # logger.debug(f"called for type {t}! Cache info: {cache_info}")

    def _get_potential_keys(annotation: str) -> List[str]:
        # Type annotation is a string.
        # This can happen when the `from __future__ import annotations` feature is used.
        potential_keys: List[Type] = []
        for key in _decoding_fns:
            if inspect.isclass(key):
                if key.__qualname__ == annotation:
                    # Qualname is more specific, there can't possibly be another match, so break.
                    potential_keys.append(key)
                    break
                if key.__qualname__ == annotation:
                    # For just __name__, there could be more than one match.
                    potential_keys.append(key)
        return potential_keys

    if isinstance(t, str):
        if t in _decoding_fns:
            return _decoding_fns[t]

        potential_keys = _get_potential_keys(t)

        if not potential_keys:
            # Try to replace the new-style annotation str with the old style syntax, and see if we
            # find a match.
            # try:
            try:
                evaluated_t = evaluate_string_annotation(t)
                # NOTE: We now have a 'live'/runtime type annotation object from the typing module.
            except (ValueError, TypeError) as err:
                logger.error(f"Unable to evaluate the type annotation string {t}: {err}.")
            else:
                if evaluated_t in _decoding_fns:
                    return _decoding_fns[evaluated_t]
                # If we still don't have this annotation stored in our dict of known functions, we
                # recurse, to try to deconstruct this annotation into its parts, and construct the
                # decoding function for the annotation. If this doesn't work, we just raise the
                # errors.
                return get_decoding_fn(evaluated_t)

            raise ValueError(
                f"Couldn't find a decoding function for the string annotation '{t}'.\n"
                f"This is probably a bug. If it is, please make an issue on GitHub so we can get "
                f"to work on fixing it.\n"
                f"Types with a known decoding function: {list(_decoding_fns.keys())}"
            )
        if len(potential_keys) == 1:
            t = potential_keys[0]
        else:
            raise ValueError(
                f"Multiple decoding functions registered for a type {t}: {potential_keys} \n"
                f"This could be a bug, but try to use different names for each type, or add the "
                f"modules they come from as a prefix, perhaps?"
            )

    if t in _decoding_fns:
        # The type has a dedicated decoding function.
        return _decoding_fns[t]

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

    from .serializable import SerializableMixin, get_dataclass_types_from_forward_ref

    if is_forward_ref(t):
        dcs = get_dataclass_types_from_forward_ref(t)
        if len(dcs) == 1:
            dc = dcs[0]
            return dc.from_dict
        if len(dcs) > 1:
            logger.warning(
                RuntimeWarning(
                    f"More than one potential Serializable dataclass was found with a name matching "
                    f"the type annotation {t}. This will simply try each one, and return the "
                    f"first one that works. Potential classes: {dcs}"
                )
            )
            return try_functions(*[partial(dc.from_dict, drop_extra_fields=False) for dc in dcs])
        else:
            # No idea what the forward ref refers to!
            logger.warning(
                f"Unable to find a dataclass that matches the forward ref {t} inside the "
                f"registered {SerializableMixin} subclasses. Leaving the value as-is."
                f"(Consider using Serializable or FrozenSerializable as a base class?)."
            )
            return no_op

    if is_typevar(t):
        bound = get_bound(t)
        logger.debug(f"Decoding a typevar: {t}, bound type is {bound}.")
        if bound is not None:
            return get_decoding_fn(bound)

    # Unknown type.
    warnings.warn(
        UserWarning(
            f"Unable to find a decoding function for the annotation {t} (of type {type(t)}). "
            f"Will try to use the type as a constructor. Consider registering a decoding function "
            f"using `register_decoding_fn`, or posting an issue on GitHub. "
        )
    )
    return try_constructor(t)


def _register(t: Type, func: Callable) -> None:
    if t not in _decoding_fns:
        # logger.debug(f"Registering the type {t} with decoding function {func}")
        _decoding_fns[t] = func


def register_decoding_fn(some_type: Type[T], function: Callable[[Any], T]) -> None:
    """Register a decoding function for the type `some_type`."""
    _register(some_type, function)


def decode_optional(t: Type[T]) -> Callable[[Optional[Any]], Optional[T]]:
    decode = get_decoding_fn(t)

    def _decode_optional(val: Optional[Any]) -> Optional[T]:
        return val if val is None else decode(val)

    return _decode_optional


def try_functions(*funcs: Callable[[Any], T]) -> Callable[[Any], Union[T, Any]]:
    """Tries to use the functions in succession, else returns the same value unchanged."""

    def _try_functions(val: Any) -> Union[T, Any]:
        e: Optional[Exception] = None
        for func in funcs:
            try:
                return func(val)
            except Exception as ex:
                e = ex
        else:
            logger.debug(f"Couldn't parse value {val}, returning it as-is. (exception: {e})")
        return val

    return _try_functions


def decode_union(*types: Type[T]) -> Callable[[Any], Union[T, Any]]:
    types = list(types)
    optional = type(None) in types
    # Partition the Union into None and non-None types.
    while type(None) in types:
        types.remove(type(None))

    decoding_fns: List[Callable[[Any], T]] = [
        decode_optional(t) if optional else get_decoding_fn(t) for t in types
    ]
    # Try using each of the non-None types, in succession. Worst case, return the value.
    return try_functions(*decoding_fns)


def decode_list(t: Type[T]) -> Callable[[List[Any]], List[T]]:
    decode_item = get_decoding_fn(t)

    def _decode_list(val: List[Any]) -> List[T]:
        return [decode_item(v) for v in val]

    return _decode_list


def decode_tuple(*tuple_item_types: Type[T]) -> Callable[[List[T]], Tuple[T, ...]]:
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

    def _decode_tuple(val: Tuple[Any, ...]) -> Tuple[T, ...]:
        if has_ellipsis:
            return tuple(decoding_fn(v) for v in val)
        else:
            return tuple(decoding_fns[i](v) for i, v in enumerate(val))

    return _decode_tuple


def decode_set(item_type: Type[T]) -> Callable[[List[T]], Set[T]]:
    """Makes a parsing function for creating sets with items of type `item_type`.

    Args:
        item_type (Type[T]): the type of the items in the set.

    Returns:
        Callable[[List[T]], Set[T]]: [description]
    """
    # Get the parse fn for a list of items of type `item_type`.
    parse_list_fn = decode_list(item_type)

    def _decode_set(val: List[Any]) -> Set[T]:
        return set(parse_list_fn(val))

    return _decode_set


def decode_dict(K_: Type[K], V_: Type[V]) -> Callable[[List[Tuple[Any, Any]]], Dict[K, V]]:
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

    def _decode_dict(val: Union[Dict[Any, Any], List[Tuple[Any, Any]]]) -> Dict[K, V]:
        result: Dict[K, V] = {}
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


def decode_enum(item_type: Type[Enum]) -> Callable[[str], Enum]:
    """
    Creates a decoding function for an enum type.

    Args:
        item_type (Type[Enum]): the type of the items in the set.

    Returns:
        Callable[[str], Enum]: A function that returns the enum member for the given name.
    """

    def _decode_enum(val: str) -> Enum:
        return item_type[val]

    return _decode_enum


def no_op(v: T) -> T:
    """Decoding function that gives back the value as-is.

    Args:
        v ([Any]): Any value.

    Returns:
        [type]: The value unchanged.
    """
    return v


def try_constructor(t: Type[T]) -> Callable[[Any], Union[T, Any]]:
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
