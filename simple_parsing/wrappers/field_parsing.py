"""Functions that are to be used to parse a field. 

Somewhat analogous to the 'parse' function in the
`helpers.serialization.parsing` package.
"""
import functools
from dataclasses import Field
from functools import lru_cache, partial
from typing import *

import typing_inspect as tpi

from ..logging_utils import get_logger
from ..utils import (get_item_type, get_type_arguments, is_dict, is_list,
                     is_optional, is_set, is_tuple, is_union, str2bool)

logger = get_logger(__file__)

T = TypeVar("T")
K = TypeVar("K")


# Dictionary mapping from types/type annotations to their parsing functions.
_parsing_fns: Dict[Type[T], Callable[[Any], T]] = {
    # the 'primitive' types are parsed using the type fn as a constructor.
    t: t for t in [str, float, int, bytes] 
}
_parsing_fns[bool] = str2bool

def get_parsing_fn_for_field(field: Field) -> Callable[[Any], T]:
    """ Gets the parsing function for the field `field`.
    """
    name = field.name
    field_type = field.type
    logger.debug(f"name = {name}, field_type = {field_type}")

    # If the user set a custom parsing function, we use it.
    custom_parsing_fn = field.metadata.get("type")
    if custom_parsing_fn is not None:
        return custom_parsing_fn

    parsing_fn = get_parsing_fn(field.type)
    return parsing_fn


def _register(t: Type, func: Callable) -> None:
    if t not in _parsing_fns:
        # logger.debug(f"Registering the type {t} with parsing function {func}")
        _parsing_fns[t] = func


def register_parsing_fn(some_type: Type[T], function: Callable[[Any], T]) -> None:
    """Register a parsing function for the type `some_type`. """
    _register(some_type, function)


def get_parsing_fn(t: Type[T]) -> Callable[[Any], T]:
    """Gets a parsing function for the given type or type annotation.

    Args:
        t (Type[T]): A type or type annotation.

    Returns:
        Callable[[Any], T]: A function that will parse a value of the given type
            from the command-line when available, or a no-op function that
            will return the raw value, when a parsing fn cannot be found or
            constructed. 
    """
    if t in _parsing_fns:
        logger.debug(f"The type {t} has a dedicated parsing function.")
        return _parsing_fns[t]

    elif t is Any:
        logger.debug(f"parsing an Any type: {t}")
        return no_op

    # TODO: Do we want to support parsing a Dict from command-line?
    # elif is_dict(t):
    #     logger.debug(f"parsing a Dict field: {t}")
    #     args = get_type_arguments(t)
    #     if len(args) != 2:
    #         args = (Any, Any)
    #     return parse_dict(*args)

    # TODO: This would require some sort of 'postprocessing' step to convert a
    # list to a Set or something like that.
    # elif is_set(t):
    #     logger.debug(f"parsing a Set field: {t}")
    #     args = get_type_arguments(t)
    #     if len(args) != 1:
    #         args = (Any,)
    #     return parse_set(args[0])

    elif is_tuple(t):
        logger.debug(f"parsing a Tuple field: {t}")
        args = get_type_arguments(t)
        parsing_fn = parse_tuple(args)
        parsing_fn.__name__ = str(t)
        return parsing_fn

    elif is_list(t):
        logger.debug(f"parsing a List field: {t}")
        args = get_type_arguments(t)
        assert len(args) == 1
        return parse_list(args[0])

    elif is_union(t):
        logger.debug(f"parsing a Union field: {t}")
        args = get_type_arguments(t)
        return parse_union(*args)

    # import typing_inspect as tpi
    # from .serializable import get_dataclass_type_from_forward_ref, Serializable

    if tpi.is_forward_ref(t):
        forward_arg = tpi.get_forward_arg(t)
        for t, fn in _parsing_fns.items():
            if getattr(t, "__name__", str(t)) == forward_arg:
                return fn

    if tpi.is_typevar(t):
        bound = tpi.get_bound(t)
        logger.debug(f"parsing a typevar: {t}, bound type is {bound}.")
        if bound is not None:
            return get_parsing_fn(bound)
    
    logger.debug(f"Couldn't find a parsing function for type {t}, will try "
                   f"to use the type directly.")
    return t


def try_functions(*funcs: Callable[[Any], T]) -> Callable[[Any], Union[T, Any]]:
    """ Tries to use the functions in succession, else returns the same value unchanged. """
    def _try_functions(val: Any) -> Union[T, Any]:
        logger.debug(f"Debugging the 'raw value' of {val}, will try functions {funcs}")
        e: Optional[Exception] = None
        for func in funcs:
            try:
                parsed = func(val)
                logger.debug(f"Successfully used the function {func} to get a parsed value of {parsed}.")
                return parsed
            except Exception as ex:
                e = ex
        else:
            logger.error(f"Couldn't parse value {val}, returning it as-is. (exception: {e})")
        return val
    return _try_functions


def parse_union(*types: Type[T]) -> Callable[[Any], Union[T, Any]]:
    types = list(types)
    optional = type(None) in types
    # Partion the Union into None and non-None types.
    while type(None) in types:
        types.remove(type(None))

    parsing_fns: List[Callable[[Any], T]] = [
        parse_optional(t) if optional else get_parsing_fn(t) for t in types
    ]
    # Try using each of the non-None types, in succession. Worst case, return the value.
    return try_functions(*parsing_fns)


def parse_optional(t: Type[T]) -> Callable[[Optional[Any]], Optional[T]]:
    parse = get_parsing_fn(t)
    def _parse_optional(val: Optional[Any]) -> Optional[T]:
        return val if val is None else parse(val)
    return _parse_optional


def parse_tuple(tuple_item_types: Tuple[Type[T], ...]) -> Callable[[List[T]], Tuple[T, ...]]:
    """Makes a parsing function for creating tuples from the command-line args.
    
    Can handle tuples with different item types, for instance:
    - `Tuple[int, Foo, str, float, ...]`.

    Returns:
        Callable[[List[T]], Tuple[T, ...]]: A parsing function for creating tuples.
    """
    # Note, if there are more values than types in the tuple type, then the
    # last type is used.
    # TODO: support the Ellipsis?
    if not tuple_item_types:
        tuple_item_types = (Any, Ellipsis)
    
    calls_count: int = 0

    def _parse_tuple(val: Any) -> Tuple[T, ...]:
        nonlocal calls_count
        logger.debug(f"Parsing a Tuple with item types {tuple_item_types}, raw value is {val}.")
        result: List[T] = []

        parsing_fn_index = calls_count

        if Ellipsis in tuple_item_types:
            ellipsis_index = tuple_item_types.index(Ellipsis)
            logger.debug(f"Ellipsis is at index {ellipsis_index}")
            # If this function is being called for the 'Ellipsis' type argument
            # or higher, just use the last type argument before the ellipsis.
            # NOTE: AFAIK, using something like Tuple[t1, t2, ...] is impossible
            # and it can only be something like Tuple[t1, ...], meaning an
            # unknown number of arguments of type `t1`.
            if parsing_fn_index >= ellipsis_index:
                parsing_fn_index = ellipsis_index - 1
        
        item_type = tuple_item_types[parsing_fn_index]
        parsing_fn = get_parsing_fn(item_type)
        parsed_value = parsing_fn(val)

        calls_count += 1
        
        return parsed_value
    
    _parse_tuple.__name__ = "BOB"

    return _parse_tuple


def parse_list(list_item_type: Type[T]) -> T:
    return get_parsing_fn(list_item_type)


def no_op(v: T) -> T:
    """Parsing function that gives back the value as-is.

    Args:
        v ([Any]): Any value.

    Returns:
        [type]: The value unchanged.
    """
    return v
