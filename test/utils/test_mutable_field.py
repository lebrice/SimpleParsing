import sys
from dataclasses import dataclass
from typing import Generic

import pytest
from typing_extensions import NamedTuple  # For Generic NamedTuples

from simple_parsing import mutable_field

from ..conftest import T, default_values_for_type, simple_arguments
from ..testutils import TestSetup


@dataclass
class A:
    a: str = "bob"


@dataclass
class B:
    # # shared_list: List = [] # not allowed.
    # different_list: List = field(default_factory=list)
    if sys.version_info < (3, 11):
        shared: A = A()
    different: A = mutable_field(A, a="123")


def test_mutable_field_sharing():
    b1 = B()
    b2 = B()
    if sys.version_info < (3, 11):
        assert b1.shared is b2.shared
    assert b1.different is not b2.different


class SimpleAttributeWithTwoDefaults(NamedTuple, Generic[T]):
    field_type: type[T]
    passed_cmdline_value: str
    expected_value: T
    default_value: T
    other_default_value: T


@pytest.fixture(
    params=[
        SimpleAttributeWithTwoDefaults(
            some_type,
            passed_value,
            expected_value,
            default_value,
            other_default_value=default_values_for_type[some_type][
                (i + 1) % len(default_values_for_type[some_type])
            ],
        )
        for some_type, passed_value, expected_value in simple_arguments
        for i, default_value in enumerate(default_values_for_type[some_type])
    ]
)
def simple_attribute_with_two_defaults(request: pytest.FixtureRequest):
    return request.param


def test_uses_default_from_field_kwargs(
    simple_attribute_with_two_defaults: SimpleAttributeWithTwoDefaults,
):
    (
        field_type,
        passed_cmdline_value,
        expected_value,
        default_value,
        other_default_value,
    ) = simple_attribute_with_two_defaults

    @dataclass
    class Inner:
        a: field_type = other_default_value  # type: ignore

    @dataclass
    class B(TestSetup):
        inner: Inner = mutable_field(Inner, a=default_value)

    assert Inner() == Inner(a=other_default_value)
    # Constructing the field works just like a regular dataclass field with a default factory:
    assert B() == B(inner=Inner(a=default_value))
    # No arguments passed: Should do the same thing:
    assert B.setup("") == B(inner=Inner(a=default_value))

    # Now, passing a value should
    assert B.setup(f"--a={passed_cmdline_value}") == B(inner=Inner(a=expected_value))
