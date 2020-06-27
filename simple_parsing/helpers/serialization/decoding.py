import inspect
# from typing import ForwardRef  # type: ignore
import itertools
import warnings
from collections import OrderedDict
from dataclasses import Field, fields, is_dataclass
from functools import lru_cache, partial
from typing import *

from ...logging_utils import get_logger
from ...utils import (get_item_type, get_type_arguments, is_dict, is_list,
                      is_tuple, is_union, is_set)

logger = get_logger(__file__)
# logger.setLevel(logging.DEBUG)
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

Dataclass = TypeVar("Dataclass")

# Dictionary mapping from types/type annotations to their decoding functions.
decoding_fns: Dict[Type, Callable[[Any], Any]] = {}


def decode_optional(t: Type[T]) -> Callable[[Optional[Any]], Optional[T]]:
    decode = _get_decoding_fn(t)

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
        decode_optional(t) if optional else _get_decoding_fn(t) for t in types
    ]
    # Try using each of the non-None types, in succession. Worst case, return the value.
    return try_functions(*decoding_fns)


def decode_list(t: Type[T]) -> Callable[[List[Any]], List[T]]:
    decode_item = _get_decoding_fn(t)

    def _decode_list(val: List[Any]) -> List[T]:
        return [decode_item(v) for v in val]
    return _decode_list


def decode_tuple(*tuple_item_types: Type[T]) -> Callable[[List[T]], Tuple[T, ...]]:
    # Get the decoding function for each item type
    decoding_fns = [
        _get_decoding_fn(t) for t in tuple_item_types
    ]

    def _decode_tuple(val: Tuple[Any, ...]) -> Tuple[T, ...]:
        return tuple(
            decoding_fns[i](v) for i, v in enumerate(val)
        )
    return _decode_tuple


def decode_set(t: Type[T]) -> Callable[[List[T]], Set[T]]:
    _decode = decode_list(t)

    def _decode_set(val: List[Any]) -> Set[T]:
        l = _decode(val)
        return set(l)
    return _decode_set


def decode_dict(K_: Type[K], V_: Type[V]) -> Callable[[List[Tuple[Any, Any]]], Dict[K, V]]:
    decode_k = _get_decoding_fn(K_)
    decode_v = _get_decoding_fn(V_)

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


def no_op(v):
    return v


def try_constructor(t: Type[T]) -> Callable[[Any], Union[T, Any]]:
    return try_functions(lambda val: t(**val))


@lru_cache(maxsize=100)
def _get_decoding_fn(t: Type[T]) -> Callable[[Any], T]:
    cache_info = _get_decoding_fn.cache_info()
    logger.debug(f"called for type {t}! Cache info: {cache_info}")

    if t in decoding_fns:
        return decoding_fns[t]
    if t in {int, str, float, bool}:
        return t

    from .serializable import Serializable
    if inspect.isclass(t) and issubclass(t, Serializable):
        return t.from_dict
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
        assert len(args) == 1
        return decode_list(args[0])

    if is_union(t):
        logger.debug(f"Decoding a Union field: {t}")
        args = get_type_arguments(t)
        return decode_union(*args)

    import typing_inspect as tpi
    from .serializable import get_dataclass_type_from_forward_ref

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
            return _get_decoding_fn(bound)
        

    # Unknown type.
    warnings.warn(UserWarning(
        f"Unable to find a decoding function for type {t}. "
        f"Will try to use the type as a constructor."
    ))
    return try_constructor(t)


def _register(t: Type, func: Callable) -> None:
    if t not in decoding_fns:
        # logger.debug(f"Registering the type {t} with decoding function {func}")
        decoding_fns[t] = func


def register_decoding_fn(some_type: Type[T], function: Callable[[Any], T]) -> None:
    """Register a decoding function for the type `some_type`.

    Because of how the decoding works, pretty much all the 
    """
    _register(some_type, function)
