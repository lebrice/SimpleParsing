""" Functions for decoding dataclass fields from "raw" values (e.g. from json).  
"""
import inspect
import itertools
import warnings
from collections import OrderedDict
from dataclasses import Field, fields, is_dataclass
from functools import lru_cache, partial
from typing import *

from ...logging_utils import get_logger
from ...utils import (get_item_type, get_type_arguments, is_dict, is_list,
                      is_set, is_tuple, is_union)

logger = get_logger(__file__)
# logger.setLevel(logging.DEBUG)
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

# Dictionary mapping from types/type annotations to their decoding functions.
_decoding_fns: Dict[Type[T], Callable[[Any], T]] = {
    # the 'primitive' types are decoded using the type fn as a constructor.
    t: t for t in [str, float, int, bool, bytes] 
}


def decode_field(field: Field, raw_value: Any) -> Any:
    """ Converts a "raw" value (e.g. from json file) to the type of the `field`.
    
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

    if t in _decoding_fns:
        # The type has a dedicated decoding function.
        return _decoding_fns[t]

    elif t is Any:
        logger.debug(f"Decoding an Any type: {t}")
        return no_op

    elif is_dict(t):
        logger.debug(f"Decoding a Dict field: {t}")
        args = get_type_arguments(t)
        if len(args) != 2:
            args = (Any, Any)
        return decode_dict(*args)

    elif is_set(t):
        logger.debug(f"Decoding a Set field: {t}")
        args = get_type_arguments(t)
        if len(args) != 1:
            args = (Any,)
        return decode_set(args[0])

    elif is_tuple(t):
        logger.debug(f"Decoding a Tuple field: {t}")
        args = get_type_arguments(t)
        return decode_tuple(*args)

    elif is_list(t):
        logger.debug(f"Decoding a List field: {t}")
        args = get_type_arguments(t)
        assert len(args) == 1
        return decode_list(args[0])

    elif is_union(t):
        logger.debug(f"Decoding a Union field: {t}")
        args = get_type_arguments(t)
        return decode_union(*args)

    import typing_inspect as tpi
    from .serializable import get_dataclass_type_from_forward_ref, Serializable

    if tpi.is_forward_ref(t):
        dc = get_dataclass_type_from_forward_ref(t)
        if dc is Serializable:
            # Since dc is Serializable, this means that we found more than one
            # matching dataclass the the given forward ref, and the right
            # subclass will be determined based on the matching fields.
            # Therefore we set drop_extra_fields=False.
            return partial(dc.from_dict, drop_extra_fields=False)
        if dc:
            return dc.from_dict

    if tpi.is_typevar(t):
        bound = tpi.get_bound(t)
        logger.debug(f"Decoding a typevar: {t}, bound type is {bound}.")
        if bound is not None:
            return get_decoding_fn(bound)
        

    # Unknown type.
    warnings.warn(UserWarning(
        f"Unable to find a decoding function for type {t}. "
        f"Will try to use the type as a constructor."
    ))
    return try_constructor(t)


def _register(t: Type, func: Callable) -> None:
    if t not in _decoding_fns:
        # logger.debug(f"Registering the type {t} with decoding function {func}")
        _decoding_fns[t] = func


def register_decoding_fn(some_type: Type[T], function: Callable[[Any], T]) -> None:
    """Register a decoding function for the type `some_type`. """
    _register(some_type, function)


def decode_optional(t: Type[T]) -> Callable[[Optional[Any]], Optional[T]]:
    decode = get_decoding_fn(t)

    def _decode_optional(val: Optional[Any]) -> Optional[T]:
        return val if val is None else decode(val)
    return _decode_optional


def try_functions(*funcs: Callable[[Any], T]) -> Callable[[Any], Union[T, Any]]:
    """ Tries to use the functions in succession, else returns the same value unchanged. """
    def _try_functions(val: Any) -> Union[T, Any]:
        e: Optional[Exception] = None
        for func in funcs:
            try:
                return func(val)
            except Exception as ex:
                e = ex
        else:
            logger.error(f"Couldn't parse value {val}, returning it as-is. (exception: {e})")
        return val
    return _try_functions


def decode_union(*types: Type[T]) -> Callable[[Any], Union[T, Any]]:
    types = list(types)
    optional = type(None) in types
    # Partion the Union into None and non-None types.
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
    decoding_fns = [
        get_decoding_fn(t) for t in tuple_item_types
    ]
    # Note, if there are more values than types in the tuple type, then the
    # last type is used.
    # TODO: support the Ellipsis?

    def _decode_tuple(val: Tuple[Any, ...]) -> Tuple[T, ...]:
        result: List[T] = []
        return tuple(
            decoding_fns[i](v) for i, v in enumerate(val)
        )
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
        else:
            items = val.items()
        for k, v in items:
            k_ = decode_k(k)
            v_ = decode_v(v)
            result[k_] = v_
        return result
    return _decode_dict


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
    return try_functions(lambda val: t(**val))
