"""Tests simple parsing decorators."""
import collections
import dataclasses
import functools
import sys
from typing import Callable

import pytest

import simple_parsing as sp


@dataclasses.dataclass
class AddThreeNumbers:
    a: int = 0
    b: int = 0
    c: int = 0

    def __call__(self) -> int:
        return self.a + self.b + self.c


def _fn_with_positional_only(x: int, /) -> int:
    return x


def _fn_with_keyword_only(*, x: int) -> int:
    return x


def _fn_with_all_argument_types(a: int, /, b: int, *, c: int) -> int:
    return a + b + c


def partial(fn: Callable, *args, **kwargs) -> Callable:
    _wrapper = functools.partial(fn, *args, **kwargs)
    _wrapper.__qualname__ = fn.__qualname__

    return _wrapper


@pytest.mark.parametrize(
    "args, expected, fn",
    [
        ("", 1, partial(_fn_with_positional_only, 1)),
        ("2", 2, partial(_fn_with_positional_only)),
        ("2", 2, _fn_with_positional_only),
        ("", 1, partial(_fn_with_keyword_only, x=1)),
        ("--x=2", 2, partial(_fn_with_keyword_only, x=1)),
        ("--x=2", 2, _fn_with_keyword_only),
        ("", 3, partial(_fn_with_all_argument_types, 1, b=1, c=1)),
        ("2", 4, partial(_fn_with_all_argument_types, b=1, c=1)),
        ("2 --b=2", 5, partial(_fn_with_all_argument_types, c=1)),
        ("2 --b=2 --c=2", 6, _fn_with_all_argument_types),
        ("--c=2", 4, partial(_fn_with_all_argument_types, 1, b=1)),
        ("--b=2", 4, partial(_fn_with_all_argument_types, 1, c=1)),
        ("--b=2 --c=2", 5, partial(_fn_with_all_argument_types, 1)),
    ],
)
def test_simple_arguments(
    args: str,
    expected: int,
    fn: Callable,
):
    decorated = sp.decorators.main(fn, args=args)
    assert decorated() == expected


def _fn_with_nested_dataclass(x: int, /, *, data: AddThreeNumbers) -> int:
    return x + data()


def _xfail_in_py311(*param):
    return pytest.param(
        *param,
        marks=pytest.mark.xfail(
            sys.version_info >= (3, 11),
            reason="TODO: test doesn't work in Python 3.11",
            strict=True,
        ),
    )


@pytest.mark.parametrize(
    "args, expected, fn",
    [
        _xfail_in_py311("", 1, partial(_fn_with_nested_dataclass, 1, data=AddThreeNumbers())),
        ("--a=1", 2, partial(_fn_with_nested_dataclass, 1)),
        ("--a=1 --b=1", 3, partial(_fn_with_nested_dataclass, 1)),
        ("--a=1 --b=1 --c=1", 4, partial(_fn_with_nested_dataclass, 1)),
        ("2 --a=1 --b=1 --c=1", 5, partial(_fn_with_nested_dataclass)),
    ],
)
def test_nested_dataclass(
    args: str,
    expected: int,
    fn: Callable,
):
    decorated = sp.decorators.main(fn, args=args)
    assert decorated() == expected
