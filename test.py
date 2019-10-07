from simple_parsing import ParseableFromCommandLine, InconsistentArgumentError
import argparse
from dataclasses import dataclass

import pytest

@dataclass
class Base(ParseableFromCommandLine):
    """A simple base-class example"""
    a: int
    b: float = 5.0
    c: str = ""

@dataclass
class Extended(Base):
    d: int = 5


def setup_base(arguments: str):
    parser = argparse.ArgumentParser()
    Base.add_arguments(parser)

    args = parser.parse_args(arguments.split())
    return args

def test_parse_base_simple_works():
    args = setup_base("--a 10 --b 3 --c Hello")
    b = Base.from_args(args)
    assert b.a == 10
    assert b.b == 3
    assert b.c == "Hello"

def test_parse_base_simple_without_required_throws_error():
    with pytest.raises(SystemExit):
        args = setup_base("--b 3 --c Hello")

def test_parse_multiple_works():
    args = setup_base("--a 10 20 --b 3 --c Hello Bye")
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
    args = setup_base("--a 10 20 --b 3 --c Hello Bye")
    with pytest.raises(InconsistentArgumentError):
        b_s = Base.from_args_multiple(args, 3)

def test_help_displays_class_docstring_text():
    from contextlib import redirect_stdout
    from io import StringIO
    f = StringIO()
    with pytest.raises(SystemExit), redirect_stdout(f):
        args = setup_base("--help")
    s = f.getvalue()
    assert Base.__doc__ in s