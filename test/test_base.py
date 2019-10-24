import argparse
import contextlib
import dataclasses
import inspect
import textwrap
from dataclasses import dataclass, field
from enum import Enum
from typing import *

import pytest
import simple_parsing
from simple_parsing import *

from .testutils import TestSetup


@pytest.mark.parametrize(
    "some_type, default_value",
    [
        (int,   123524),
        (float, 123.456),
        (str,   "bob"),
        (bool,  True),
    ]
)
def test_default_value_is_used_when_no_args_are_provided(some_type: Type, default_value):
    @dataclass()
    class SomeClass(TestSetup):
        a: some_type = default_value # type: ignore
        """some docstring for attribute 'a'"""
    
    class_a = SomeClass.setup()
    assert class_a.a == default_value
    assert isinstance(class_a.a, some_type)


@pytest.mark.parametrize(
    "some_type, default_value,  arg_value",
    [
        (int,   0,      1234),
        (float, 0.,     123.456),
        (str,   "",     "bobby_boots"),
        (bool,  False,  True),
    ])
def test_arg_value_is_set_when_args_are_provided(some_type: Type, default_value: Any, arg_value: Any):
    @dataclass()
    class SomeClass(TestSetup):
        a: some_type = default_value # type: ignore
        """some docstring for attribute 'a'"""

    class_a = SomeClass.setup(f"--a {arg_value}")
    assert class_a.a != default_value
    assert class_a.a == arg_value
    assert isinstance(class_a.a, some_type)


@pytest.mark.parametrize("some_type", [int, float, str, bool,])
def test_not_providing_required_argument_throws_error(some_type):
    @dataclass()
    class SomeClass(ParseableFromCommandLine, TestSetup):
        a: some_type # type: ignore
        """some docstring for attribute 'a'"""
    with pytest.raises(SystemExit):
        class_a = SomeClass.setup("")


@pytest.mark.parametrize("some_type", [int, float, str])
def test_not_providing_required_argument_name_but_no_value_throws_error(some_type):
    @dataclass()
    class SomeClass(ParseableFromCommandLine, TestSetup):
        a: some_type # type: ignore
        """some docstring for attribute 'a'"""

    with pytest.raises(SystemExit):
        class_a = SomeClass.setup("--a")

class Color(Enum):
    RED = "RED"
    ORANGE = "ORANGE"
    BLUE = "BLUE"

@dataclass()
class Base(TestSetup):
    """A simple base-class example"""
    a: int # TODO: finetune this
    """docstring for attribute 'a'"""
    b: float = 5.0 # inline comment on attribute 'b'
    c: str = ""

@dataclass()
class Extended(Base):
    """ Some extension of base-class `Base` """
    d: int = 5
    """ docstring for 'd' in Extended. """
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
    with pytest.raises(InconsistentArgumentError):
        args = Base.setup_multiple(3, "--a 10 20 --b 3 --c Hello Bye")

def test_help_displays_class_docstring_text():
    assert Base.__doc__ in Base.get_help_text()

def test_enum_attributes_work():
    ext = Extended.setup("--a 5 --e RED")
    assert ext.e == Color.RED

    ext = Extended.setup("--a 5")
    assert ext.e == Color.BLUE
