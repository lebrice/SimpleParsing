import argparse
import shlex
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import pytest

import simple_parsing
from simple_parsing import ArgumentParser

from .testutils import TestSetup, parametrize, raises, raises_missing_required_arg


def test_basic_required_argument(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeDataclass(TestSetup):
        some_attribute: some_type  # type: ignore

    actual = SomeDataclass.setup(f"--some_attribute {passed_value}")
    assert actual.some_attribute == expected_value
    assert isinstance(actual.some_attribute, some_type)


def test_not_passing_required_argument_raises_error(simple_attribute):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeDataclass(TestSetup):
        some_attribute: some_type  # type: ignore

    with raises_missing_required_arg():
        _ = SomeDataclass.setup("")


def test_basic_optional_argument(simple_attribute, silent):
    some_type, _, expected_value = simple_attribute

    @dataclass
    class SomeDataclass(TestSetup):
        some_attribute: some_type = expected_value  # type: ignore

    actual = SomeDataclass.setup("")
    assert actual.some_attribute == expected_value
    assert isinstance(actual.some_attribute, some_type)


def test_works_fine_with_other_argparse_arguments(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type  # type: ignore
        """Some docstring for attribute 'a'."""

    parser = ArgumentParser()
    parser.add_argument("--x", type=int)
    parser.add_arguments(SomeClass, dest="some_class")

    x = 123
    args = parser.parse_args(shlex.split(f"--x {x} --a {passed_value}"))
    assert args == argparse.Namespace(some_class=SomeClass(a=expected_value), x=x)


@parametrize(
    "some_type, default_value,  arg_value",
    [
        (int, 0, 1234),
        (float, 0.0, 123.456),
        (str, "", "bobby_boots"),
        (bool, False, True),
    ],
)
def test_arg_value_is_set_when_args_are_provided(
    some_type: type, default_value: Any, arg_value: Any
):
    @dataclass
    class SomeClass(TestSetup):
        a: some_type = default_value  # type: ignore
        """Some docstring for attribute 'a'."""

    class_a = SomeClass.setup(f"--a {arg_value}")
    assert class_a.a != default_value
    assert class_a.a == arg_value
    assert isinstance(class_a.a, some_type)


@parametrize(
    "some_type",
    [
        int,
        float,
        str,
        bool,
    ],
)
def test_not_providing_required_argument_throws_error(some_type):
    @dataclass
    class SomeClass(TestSetup):
        a: some_type  # type: ignore
        """Some docstring for attribute 'a'."""

    with raises(SystemExit):
        _ = SomeClass.setup("")


@parametrize("some_type", [int, float, str])
def test_not_providing_required_argument_name_but_no_value_throws_error(some_type):
    @dataclass
    class SomeClass(TestSetup):
        a: some_type  # type: ignore
        """Some docstring for attribute 'a'."""

    with raises(SystemExit):
        _ = SomeClass.setup("--a")


class Color(Enum):
    RED = "RED"
    ORANGE = "ORANGE"
    BLUE = "BLUE"


@dataclass
class Base(TestSetup):
    """A simple base-class example."""

    a: int  # TODO: finetune this
    """Docstring for attribute 'a'."""
    b: float = 5.0  # inline comment on attribute 'b'
    c: str = ""


@dataclass
class Extended(Base):
    """Some extension of base-class `Base`"""

    d: int = 5
    """Docstring for 'd' in Extended."""
    e: Color = Color.BLUE


def test_parse_base_simple_works():
    b = Base.setup("--a 10 --b 3 --c Hello")
    assert b.a == 10
    assert b.b == 3
    assert b.c == "Hello"


def test_parse_multiple_works():
    b1, b2 = Base.setup_multiple(2, "--a 10 20 --b 3 --c Hello Bye")
    assert b1.a == 10
    assert b1.b == 3
    assert b1.c == "Hello"

    assert b2.a == 20
    assert b2.b == 3
    assert b2.c == "Bye"


def test_parse_multiple_inconsistent_throws_error():
    with pytest.raises(simple_parsing.InconsistentArgumentError):
        _ = Base.setup_multiple(3, "--a 10 20 --b 3 --c Hello Bye")


def test_help_displays_class_docstring_text():
    assert Base.__doc__ in Base.get_help_text()


def test_enum_attributes_work():
    ext = Extended.setup("--a 5 --e RED")
    assert ext.e == Color.RED

    ext = Extended.setup("--a 5")
    assert ext.e == Color.BLUE


def test_passing_default_value(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass(TestSetup):
        a: some_type = passed_value  # type: ignore
        """Some docstring for attribute 'a'."""

    some_class = SomeClass.setup(default=SomeClass(expected_value))
    assert some_class.a == expected_value


def test_parsing_twice():
    @dataclass
    class Foo:
        a: int = 123

    parser = ArgumentParser()
    parser.add_arguments(Foo, dest="foo")
    args = parser.parse_args("")
    assert args.foo.a == 123, vars(args)
    args = parser.parse_args("--a 456".split())
    assert args.foo.a == 456, vars(args)


def test_passing_instance():
    @dataclass
    class Foo:
        a: int = 123

    parser = ArgumentParser()
    parser.add_arguments(Foo(456), dest="foo")
    args = parser.parse_args("")
    assert args.foo.a == 456, vars(args)


def test_using_a_Type_type():
    @dataclass
    class Base:
        a: str = "a"

    @dataclass
    class Extended(Base):
        a: str = "extended_a"

    @dataclass
    class Foo(TestSetup):
        a_class: type[Base] = field(default=Base, init=False)
        a: Base = field(default=None, init=False)

        def __post_init__(self):
            self.a = self.a_class()

    foo = Foo.setup("")
    from simple_parsing.utils import contains_dataclass_type_arg

    assert not contains_dataclass_type_arg(type[Base])
    assert foo.a_class() == Base()

    @dataclass
    class OtherFoo(Foo):
        a_class: type[Base] = field(default=Extended, init=False)

    foo = OtherFoo.setup("")
    assert foo.a == Extended()


def test_issue62():
    import enum

    from simple_parsing.helpers import list_field

    parser = ArgumentParser()

    class Color(enum.Enum):
        RED = "red"
        ORANGE = "orange"
        BLUE = "blue"

    class Temperature(enum.Enum):
        HOT = 1
        WARM = 0
        COLD = -1
        MONTREAL = -35

    @dataclass
    class MyPreferences(TestSetup):
        """You can use Enums."""

        color: Color = Color.BLUE  # my favorite colour
        # a list of colors
        color_list: list[Color] = list_field(Color.ORANGE)
        # Some floats.
        floats: list[float] = list_field(1.1, 2.2, 3.3)
        # pick a temperature
        temp: Temperature = Temperature.WARM
        # a list of temperatures
        temp_list: list[Temperature] = list_field(Temperature.COLD, Temperature.WARM)

    parser.add_arguments(MyPreferences, "my_preferences")
    assert MyPreferences.setup(
        "--color ORANGE --color_list RED BLUE --temp MONTREAL"
    ) == MyPreferences(
        color=Color.ORANGE,
        color_list=[Color.RED, Color.BLUE],
        temp=Temperature.MONTREAL,
        temp_list=[Temperature.COLD, Temperature.WARM],
    )
    assert MyPreferences.setup(
        "--color ORANGE --color_list RED BLUE --temp MONTREAL --temp_list MONTREAL HOT"
    ) == MyPreferences(
        color=Color.ORANGE,
        color_list=[Color.RED, Color.BLUE],
        temp=Temperature.MONTREAL,
        temp_list=[Temperature.MONTREAL, Temperature.HOT],
    )
    assert Temperature["MONTREAL"] is Temperature.MONTREAL
    assert Temperature(-35) is Temperature.MONTREAL

    # NOTE: This kind of test (comparing the help str) is unreliable, changes depending on the
    # python version.
    # assert MyPreferences.get_help_text() == textwrap.dedent("""\
    #     usage: pytest [-h] [--color Color] [--color_list Color] [--floats float]
    #                   [--temp Temperature] [--temp_list Temperature]

    #     optional arguments:
    #       -h, --help            show this help message and exit

    #     test_issue62.<locals>.MyPreferences ['my_preferences']:
    #       You can use Enums

    #       --color Color         my favorite colour (default: BLUE)
    #       --color_list Color    a list of colors (default: [<Color.ORANGE: 'orange'>])
    #       --floats float        Some floats. (default: [1.1, 2.2, 3.3])
    #       --temp Temperature    pick a temperature (default: WARM)
    #       --temp_list Temperature
    #                             a list of temperatures (default: [<Temperature.COLD:
    #                             -1>, <Temperature.WARM: 0>])
    # """)
