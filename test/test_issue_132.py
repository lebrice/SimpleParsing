"""Test for https://github.com/lebrice/SimpleParsing/issues/132."""
from dataclasses import dataclass

from simple_parsing import field

from .conftest import SimpleAttributeTuple
from .testutils import TestSetup


def test_field_with_custom_required_arg_is_optional(
    simple_attribute: SimpleAttributeTuple,
):
    """Test that the `field` function can be used as a work-around for issue 132.

    When passing `required` (or any other of the usual arguments of `parser.add_argument`) to the
    `field` function, they get saved into the `FieldWrapper`, and used to populate the args_dict
    that gets passed to `parser.add_arguments(*field_wrapper.option_strings, **args_dict)`.

    Therefore, using `required=False` as a custom argument is a work-around, while we fix this
    issue.
    """
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class Foo(TestSetup):
        a: some_type = field(default=None, required=False)  # type: ignore

    assert Foo.setup() == Foo(a=None)
    assert Foo.setup(f"--a {passed_value}") == Foo(a=expected_value)


def test_field_with_none_default_is_optional(simple_attribute: SimpleAttributeTuple):
    """Test that when the default value is None, the argument is treated as optional."""
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class Foo(TestSetup):
        a: some_type = None  # type: ignore

    assert Foo.setup() == Foo(a=None)
    assert Foo.setup(f"--a {passed_value}") == Foo(a=expected_value)


def test_dataclass_field_with_none_default_is_optional(
    simple_attribute: SimpleAttributeTuple,
):
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
