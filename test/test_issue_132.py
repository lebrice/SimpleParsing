""" Test for https://github.com/lebrice/SimpleParsing/issues/132 """
from dataclasses import dataclass

from .conftest import SimpleAttributeTuple
from .testutils import TestSetup


def test_field_with_none_default_is_optional(simple_attribute: SimpleAttributeTuple):
    """Test that when the default value is None, the argument is treated as optional."""
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class Foo(TestSetup):
        a: some_type = None  # type: ignore

    assert Foo.setup() == Foo(a=None)
    assert Foo.setup(f"--a {passed_value}") == Foo(a=expected_value)


def test_dataclass_field_with_none_default_is_optional(simple_attribute: SimpleAttributeTuple):
    """Test that when the default value is None, the argument is treated as optional."""
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class Foo(TestSetup):
        a: some_type  # type: ignore

    @dataclass
    class Bar(TestSetup):
        foo: Foo = None  # type: ignore

    assert Bar.setup() == Bar(foo=None)  # type: ignore
    assert Bar.setup(f"--a {passed_value}") == Bar(foo=Foo(a=expected_value))
