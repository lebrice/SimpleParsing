"""Tests simple parsing decorators."""
import collections
import dataclasses
import functools
import inspect
import sys
import typing
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


class ListWithPopDefault(collections.UserList):
    def pop(self, index, default_value=None):
        try:
            return super().pop(index)
        except IndexError:
            return default_value


def change_defaults(fn: Callable, *args, **kwargs) -> Callable:
    """Partial via changing the signature defaults."""

    @functools.wraps(fn)
    def _wrapper(*other_args, **other_kwargs):
        return fn(*other_args, **other_kwargs)

    signature = inspect.signature(fn)
    parameters = signature.parameters

    args = ListWithPopDefault(args)

    new_parameters = []
    for key, param in parameters.items():
        param = typing.cast(inspect.Parameter, param)
        default = args.pop(0, None) or kwargs.get(key, None)
        if default is not None:
            param = param.replace(default=default)
        new_parameters.append(param)

    signature = signature.replace(parameters=new_parameters)
    _wrapper.__signature__ = signature

    return _wrapper


def _xfail_in_py311(*param):
    return pytest.param(
        *param,
        marks=pytest.mark.xfail(
            sys.version_info >= (3, 11),
            reason="TODO: test doesn't work in Python 3.11",
            raises=ValueError,  # "non-default argument follows default argument"
            strict=True,
        ),
    )


@pytest.mark.parametrize(
    "args, expected, fn",
    [
        ("", 1, change_defaults(_fn_with_positional_only, 1)),
        ("2", 2, change_defaults(_fn_with_positional_only, 1)),
        ("2", 2, change_defaults(_fn_with_positional_only)),
        ("", 1, change_defaults(_fn_with_keyword_only, x=1)),
        ("--x=2", 2, change_defaults(_fn_with_keyword_only, x=1)),
        ("--x=2", 2, change_defaults(_fn_with_keyword_only)),
        ("", 3, change_defaults(_fn_with_all_argument_types, 1, b=1, c=1)),
        ("2", 4, change_defaults(_fn_with_all_argument_types, b=1, c=1)),
        ("2 --b=2", 5, change_defaults(_fn_with_all_argument_types, c=1)),
        ("2 --b=2 --c=2", 6, change_defaults(_fn_with_all_argument_types)),
        ("--c=2", 4, change_defaults(_fn_with_all_argument_types, 1, b=1)),
        _xfail_in_py311(
            "--b=2", 4, functools.partial(change_defaults, _fn_with_all_argument_types, 1, c=1)
        ),
        _xfail_in_py311(
            "--b=2 --c=2", 5, functools.partial(change_defaults, _fn_with_all_argument_types, 1)
        ),
    ],
)
def test_simple_arguments(
    args: str,
    expected: int,
    fn: Callable,
):
    if isinstance(fn, functools.partial):
        # In Python 3.11.4, the inspect module had a backward-incompatible change. We need to have
        # this additional level of indirection.
        fn = fn()
    decorated = sp.decorators.main(fn, args=args)
    assert decorated() == expected


def _fn_with_nested_dataclass(x: int, /, *, data: AddThreeNumbers) -> int:
    return x + data()


@pytest.mark.parametrize(
    ("args", "expected", "fn"),
    [
        _xfail_in_py311(
            "", 1, change_defaults(_fn_with_nested_dataclass, 1, data=AddThreeNumbers())
        ),
        ("--a=1", 2, change_defaults(_fn_with_nested_dataclass, 1)),
        ("--a=1 --b=1", 3, change_defaults(_fn_with_nested_dataclass, 1)),
        ("--a=1 --b=1 --c=1", 4, change_defaults(_fn_with_nested_dataclass, 1)),
        ("2 --a=1 --b=1 --c=1", 5, change_defaults(_fn_with_nested_dataclass)),
    ],
)
def test_nested_dataclass(
    args: str,
    expected: int,
    fn: Callable,
):
    decorated = sp.decorators.main(fn, args=args)
    assert decorated() == expected
