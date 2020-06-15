import inspect
# from typing import ForwardRef  # type: ignore
import itertools
import logging
import warnings
from collections import OrderedDict
from dataclasses import Field, fields, is_dataclass
from typing import *

import typing_inspect as tpi

logger = logging.getLogger(__file__)
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


def decode_list(t: Type[T]) -> Callable[[List[Any]], List[T]]:
    decode_item = _get_decoding_fn(t)
    def _decode_list(val: List[Any]) -> List[T]:
        return [decode_item(v) for v in val]
    return _decode_list


def decode_dict(K_: Type[K], V_: Type[V], dict_factory: Type[Dict]=dict) -> Callable[[Dict[Any, Any]], Dict[K, V]]:
    decode_key = _get_decoding_fn(K_)
    decode_value = _get_decoding_fn(V_)
    def _decode_dict(value: Dict[Any, Any]) -> Dict[K, V]:
        result: Dict[K, V] = dict_factory()
        for k, v in value.items():
            k_ = decode_key(k)
            v_ = decode_value(v)
            result[k_] = v_
        return result
    return _decode_dict


def no_op(v):
    return v

def try_constructor(t: Type[T]) -> Callable[[Any], Union[T, Any]]:
    def try_parse(val: Any) -> Union[T, Any]:
        try:
            return t(val)  # type: ignore
        except Exception as e:
            logging.error(f"Couldn't parse value {val} into an instance of type {t} using the type as a constructor: {e}")
            return val
    return try_parse

def _get_decoding_fn(t: Type[T]) -> Callable[[Any], T]:
    if t in decoding_fns:
        return decoding_fns[t]
    elif t in {int, str, float, bool}:
        return t
    warnings.warn(UserWarning(f"Unable to find a decoding function for type {t}. Will try to use the type as a constructor."))
    return try_constructor(t)


def _register(t: Type, func: Callable) -> None:
    if t not in decoding_fns:
        logger.debug(f"Registering the type {t} with decoding function {func}")
        decoding_fns[t] = func


def register_decoding_fn(some_type: Type[T], function: Callable[[Any], T], add_variants: bool=True) -> None:
    """Register a decoding function for the type `some_type`.
    
    If `add_variants` is `True`, then also adds variants for the types:
    - Optional[some_type]
    - Optional[List[some_type]]
    - List[some_type]
    - List[Optional[some_type]]
    - List[List[some_type]]
    - List[List[Optional[some_type]]]

    NOTE: `Dict[<k>, <any of the above>]` should also be supported given how
    `from_dict` is implemented below, but I didn't test out every combination.

    #TODO: Could maybe use a different approach, where we seek out the right
    # decoding function in a 'top-down' approach. So for instance, if we
    # encounter a List[<T>], we check for <T>. if T is Dict[<K>, <V>], we check
    # for <K>, then <V>, recursively, etc. The benefit is that we wouldn't have
    # to manually create the decoding functions for all the variants. 
    """
    _register(some_type, function)

    if add_variants:
        _register(Optional[some_type],  decode_optional(some_type))
        _register(List[some_type],      decode_list(some_type))  # type: ignore
        _register(List[some_type],      decode_list(some_type))  # type: ignore
        _register(Dict[int, some_type], decode_dict(int, some_type))  # type: ignore
        _register(Dict[str, some_type], decode_dict(str, some_type))  # type: ignore
        # _register(ForwardRef(some_type.__name__), decoding_fns[some_type])

        variants: List[Type] = [
            some_type,
            Optional[some_type],
            List[some_type],  # type: ignore
            List[Optional[some_type]],  # type: ignore
            Optional[List[some_type]],  # type: ignore
            # ForwardRef(some_type.__name__),
        ]

        for item_type in variants:
            # Register decoders for Optional[<variant>]
            _register(Optional[item_type], decode_optional(item_type))  # type: ignore
            # Register decoders for List[<variant>]
            _register(List[item_type], decode_list(item_type))  # type: ignore

        key_types: List[Type] = [int, str]
        # Register decoders for Dict<K>, <variant>]
        for key_type, value_type in itertools.product(key_types, variants):
            logger.debug(f"Registering K: {key_type}, V: {value_type}")
            decoding_fn = decode_dict(key_type, value_type)
            _register(Dict[key_type, value_type], decoding_fn)  # type: ignore
            _register(Mapping[key_type, value_type], decoding_fn)  # type: ignore
            _register(MutableMapping[key_type, value_type], decoding_fn)  # type: ignore

        # for item in variants:
        #     if hasattr(item, "__name__"):
        #         _register(ForwardRef(item.__name__), decoding_fns[item])


