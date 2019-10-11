import argparse
import contextlib
import dataclasses
import inspect
import textwrap
from dataclasses import dataclass, field
from enum import Enum
from typing import *

import pytest
from simple_parsing import InconsistentArgumentError, ParseableFromCommandLine


class Setup():
    @classmethod
    def setup(cls: ParseableFromCommandLine, arguments = "", multiple = False) -> str:
        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        cls.add_arguments(parser, multiple=multiple)
        args = parser.parse_args(arguments.split())
        return args
    
    @classmethod
    def get_help_text(cls: ParseableFromCommandLine, multiple=False):
        import contextlib
        from io import StringIO
        f = StringIO()
        with contextlib.suppress(SystemExit), contextlib.redirect_stdout(f):
            _ = cls.setup("--help")
        s = f.getvalue()
        return s


@dataclass
class Base(ParseableFromCommandLine, Setup):
    """A simple base-class example"""
    a: int # TODO: finetune this
    """docstring for attribute 'a'"""
    b: float = 5.0 # inline comment on attribute 'b'
    c: str = ""

class Color(Enum):
    RED = "RED"
    ORANGE = "ORANGE"
    BLUE = "BLUE"

@dataclass
class Extended(Base):
    """ Some extension of base-class `Base` """
    d: int = 5
    """ docstring for 'd' in Extended. """
    e: Color = Color.BLUE
    f: bool = False


@dataclass
class Container(ParseableFromCommandLine, Setup):
    a: Tuple[int]
    b: List[int]
    c: Tuple[str] = field(default_factory=tuple)
    d: List[int] = field(default_factory=list)

@dataclass
class Flags(ParseableFromCommandLine, Setup):
    a: bool # an example required flag (defaults to False)
    b: bool = True # optional flag 'b'.
    c: bool = False # optional flag 'c'.

def test_parse_base_simple_works():
    args = Base.setup("--a 10 --b 3 --c Hello")
    b = Base.from_args(args)
    assert b.a == 10
    assert b.b == 3
    assert b.c == "Hello"

def test_parse_base_simple_without_required_throws_error():
    with pytest.raises(SystemExit):
        args = Base.setup("--b 3 --c Hello")

def test_parse_multiple_works():
    args = Base.setup("--a 10 20 --b 3 --c Hello Bye", multiple=True)
    b_s = Base.from_args_multiple(args, 2)
    b1 = b_s[0]
    b2 = b_s[1]
    assert b1.a == 10
    assert b1.b == 3
    assert b1.c == "Hello"

    assert b2.a == 20
    assert b2.b == 3
    assert b2.c == "Bye"

def test_parse_multiple_inconsistent_throws_error():
    args = Base.setup("--a 10 20 --b 3 --c Hello Bye", multiple=True)
    with pytest.raises(InconsistentArgumentError):
        b_s = Base.from_args_multiple(args, 3)


def test_help_displays_class_docstring_text():
    assert Base.__doc__ in Base.get_help_text()


def test_enum_attributes_work():
    args = Extended.setup("--a 5 --e RED")
    ext = Extended.from_args(args)
    assert ext.e == Color.RED

    args = Extended.setup("--a 5")
    ext = Extended.from_args(args)
    assert ext.e == Color.BLUE


def test_bool_attributes_work():
    args = Extended.setup("--a 5 --f")
    ext = Extended.from_args(args)
    assert ext.f == True

    args = Extended.setup("--a 5")
    ext = Extended.from_args(args)
    assert ext.f == False

    true_strings = ["True", "true"]
    for s in true_strings:
        args = Extended.setup(f"--a 5 --f {s}")
        ext = Extended.from_args(args)
        assert ext.f == True

    false_strings = ["False", "false"]
    for s in false_strings:
        args = Extended.setup(f"--a 5 --f {s}")
        ext = Extended.from_args(args)
        assert ext.f == False


def test_bool_flags_work():
    args = Flags.setup("--a true --b --c")
    flags = Flags.from_args(args)
    assert flags.a == True
    assert flags.b == False
    assert flags.c == True


def test_list_attributes_work():
    args = Container.setup("--a 1 2 3 --b 4 5 6 --c 7 8 9 --d 10 11 12")
    container = Container.from_args(args)
    assert container.a == (1, 2, 3)
    assert container.b == [4, 5, 6]
    assert container.c == ('7', '8', '9')
    assert container.d == [10, 11, 12]

    # required attributes still work.
    with contextlib.suppress(SystemExit), pytest.raises(argparse.ArgumentError):
        args = Container.setup("--b 4")

    args = Container.setup("--a 1 2 --b 2 --c 3 4 5 --d 10 11 12")
    container = Container.from_args(args)
    assert container.a == (1,2)
    assert container.b == [2]
    assert container.c == ('3', '4', '5')
    assert container.d == [10, 11, 12]

def main(some_class: ParseableFromCommandLine):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    some_class.add_arguments(parser, multiple=False)
    args = parser.parse_args()
    obj = some_class.from_args(args)
    print(obj)

if __name__ == "__main__":
    main(Flags)
