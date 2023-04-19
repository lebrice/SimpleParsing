import functools
from typing import Any, Generic, TypeVar

_T = TypeVar("_T")


class npartial(functools.partial, Generic[_T]):
    """Partial that also invokes partials in args and kwargs before feeding them to the function.

    Useful for creating nested partials, e.g.:


    >>> from dataclasses import dataclass, field
    >>> @dataclass
    ... class Value:
    ...    v: int = 0
    >>> @dataclass
    ... class ValueWrapper:
    ...    value: Value
    ...
    >>> from functools import partial
    >>> @dataclass
    ... class WithRegularPartial:
    ...    wrapped: ValueWrapper = field(
    ...        default_factory=partial(ValueWrapper, value=Value(v=123)),
    ...    )

    Here's the problem: This here is BAD! They both share the same instance of Value!

    >>> WithRegularPartial().wrapped.value is WithRegularPartial().wrapped.value
    True
    >>> @dataclass
    ... class WithNPartial:
    ...    wrapped: ValueWrapper = field(
    ...        default_factory=npartial(ValueWrapper, value=npartial(Value, v=123)),
    ...    )
    >>> WithNPartial().wrapped.value is WithNPartial().wrapped.value
    False

    This is fine now!
    """

    def __call__(self, *args: Any, **keywords: Any) -> _T:
        keywords = {**self.keywords, **keywords}
        args = self.args + args
        args = tuple(arg() if isinstance(arg, npartial) else arg for arg in args)
        keywords = {k: v() if isinstance(v, npartial) else v for k, v in keywords.items()}
        return self.func(*args, **keywords)
