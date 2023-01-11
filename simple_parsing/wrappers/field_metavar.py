import functools
from logging import getLogger
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from ..utils import get_type_arguments, is_optional, is_tuple, is_union

T = TypeVar("T")

logger = getLogger(__name__)

_new_metavars: Dict[Type[T], Optional[str]] = {
    # the 'primitive' types don't get a 'new' metavar.
    t: t.__name__
    for t in [str, float, int, bytes]
}


def log_results(fn: Callable[[Type], str]):
    @functools.wraps(fn)
    def _wrapped(t: Type) -> str:
        result = fn(t)
        # logger.debug(f"Metavar for type {t}: {result}")
        return result

    return _wrapped


@log_results
def get_metavar(t: Type) -> str:
    """Gets the metavar to be used for that type in help strings.

    This is crucial when using a `weird` auto-generated parsing functions for
    things like Union, Optional, Etc etc.

    type the type arguments that were passed to `get_parsing_fn` that
    produced the given parsing_fn.

    returns None if the name shouldn't be changed.
    """
    # TODO: Maybe we can create the name for each returned call, a bit like how
    # we dynamically create the parsing function itself?
    new_name: str = getattr(t, "__name__", None)

    optional = is_optional(t)

    if t in _new_metavars:
        return _new_metavars[t]

    elif is_union(t):
        args = get_type_arguments(t)
        metavars: List[str] = []
        for type_arg in args:
            if type_arg is type(None):  # noqa: E721
                continue
            metavars.append(get_metavar(type_arg))
        metavar = "|".join(map(str, metavars))
        if optional:
            return f"[{metavar}]"
        return metavar

    elif is_tuple(t):
        args = get_type_arguments(t)
        if not args:
            return get_metavar(Any)
        logger.debug(f"Tuple args: {args}")
        metavars: List[str] = []
        for arg in args:
            if arg is Ellipsis:
                metavars.append(f"[{metavars[-1]}, ...]")
                break
            else:
                metavars.append(get_metavar(arg))
        return " ".join(metavars)

    return new_name
