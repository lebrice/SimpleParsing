"""Functions that are to be used to parse a field.

Somewhat analogous to the 'parse' function in the `helpers.serialization.parsing` package.
"""
import enum
import functools
from dataclasses import Field
from logging import getLogger
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar, Union

from simple_parsing.utils import (
    get_bound,
    get_forward_arg,
    get_type_arguments,
    is_enum,
    is_forward_ref,
    is_homogeneous_tuple_type,
    is_list,
    is_tuple,
    is_typevar,
    is_union,
    str2bool,
)

logger = getLogger(__name__)

T = TypeVar("T")
K = TypeVar("K")


# Dictionary mapping from types/type annotations to their parsing functions.
_parsing_fns: Dict[Type[T], Callable[[Any], T]] = {
    # the 'primitive' types are parsed using the type fn as a constructor.
    t: t
    for t in [str, float, int, bytes]
}
_parsing_fns[bool] = str2bool


def get_parsing_fn_for_field(field: Field) -> Callable[[Any], T]:
    """Gets the parsing function for the field `field`."""
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
    """Register a parsing function for the type `some_type`."""
    _register(some_type, function)


# This doesn't work as well as it did for serialization, in large part due to how
# argparse uses the `type` function when parsing containers.
# TODO: Replace this with a simpler function that just returns the 'arg_options' dict to
# give for a given type annotation.
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
        if is_homogeneous_tuple_type(t):
            if not args:
                args = (str, ...)
            parsing_fn = get_parsing_fn(args[0])
        else:
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

    elif is_enum(t):
        logger.debug(f"Parsing an Enum field of type {t}")
        return parse_enum(t)

    if is_forward_ref(t):
        forward_arg = get_forward_arg(t)
        for t, fn in _parsing_fns.items():
            if getattr(t, "__name__", str(t)) == forward_arg:
                return fn

    if is_typevar(t):
        bound = get_bound(t)
        logger.debug(f"parsing a typevar: {t}, bound type is {bound}.")
        if bound is not None:
            return get_parsing_fn(bound)

    logger.debug(
        f"Couldn't find a parsing function for type {t}, will try " f"to use the type directly."
    )
    return t


def try_functions(*funcs: Callable[[Any], T]) -> Callable[[Any], Union[T, Any]]:
    """Tries to use the functions in succession, else raises a ValueError."""

    def _try_functions(val: Any) -> Union[T, Any]:
        logger.debug(f"Debugging the 'raw value' of {val}, will try functions {funcs}")
        exceptions: list[Exception] = []
        for func in funcs:
            try:
                parsed = func(val)
                logger.debug(
                    f"Successfully used the function {func} to get a parsed value of {parsed}."
                )
                return parsed
            except Exception as ex:
                exceptions.append(ex)
        logger.error(
            f"Couldn't parse value {val}, returning the value as-is. (exceptions: {exceptions})"
        )
        raise ValueError(
            f"Couldn't parse value {val}, returning the value as-is. (exceptions: {exceptions})"
        )

    _try_functions.__name__ = (
        "Try<" + " and ".join(str(getattr(func, "__name__", func)) for func in funcs) + ">"
    )
    return _try_functions


def parse_union(*types: Type[T]) -> Callable[[Any], Union[T, Any]]:
    types = list(types)
    optional = type(None) in types
    # Partition the Union into None and non-None types.
    while type(None) in types:
        types.remove(type(None))

    parsing_fns: List[Callable[[Any], T]] = [
        parse_optional(t) if optional else get_parsing_fn(t) for t in types
    ]
    # Try using each of the non-None types, in succession. Worst case, return the value.
    f = try_functions(*parsing_fns)
    from simple_parsing.wrappers.field_metavar import get_metavar

    f.__name__ = get_metavar(Union[tuple(types)])  # type: ignore
    # f.__name__ = "|".join(str(t.__name__) for t in types)
    return f


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


E = TypeVar("E", bound=enum.Enum)


def parse_enum(enum_type: Type[E]) -> Callable[[str], E]:
    """Returns a function to use to parse an enum of type `enum_type` from a string.

    Parameters
    ----------
    - enum_type : Type[enum.Enum]

        The type of enum to create a parsing function for.

    Returns
    -------
    Callable[[str], E]
        A function that parses an enum object of type `enum_type` from a string.
    """
    # Save the function, since the same type will always be parsed the same way. Also
    # makes testing easier.
    if enum_type in _parsing_fns:
        return _parsing_fns[enum_type]

    # NOTE: Use `functools.wraps` so that fn name is the enum, so the metavar shows up
    # just like the enum on the command-line, and not like
    # "(...).parse_enum.<locals>._parse_enum" or something.
    @functools.wraps(enum_type)
    def _parse_enum(v: str) -> E:
        return enum_type[v]

    _parsing_fns[enum_type] = _parse_enum
    return _parse_enum
