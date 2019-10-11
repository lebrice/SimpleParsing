from simple_parsing import ParseableFromCommandLine, InconsistentArgumentError
import argparse
import dataclasses
from dataclasses import dataclass, Field

import pytest
import inspect
import textwrap

@dataclass
class Base(ParseableFromCommandLine):
    """A simple base-class example"""
    a: int # TODO: finetune this
    """docstring for attribute 'a'"""
    b: float = 5.0 # inline comment on attribute 'b'
    c: str = ""

@dataclass
class Extended(Base):
    """ Some extension of base-class `Base` """
    d: int = 5
    """ docstring for 'd' in Extended. """


def setup_base(arguments: str, multiple=False):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    Base.add_arguments(parser, multiple=multiple)

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
    args = setup_base("--a 10 20 --b 3 --c Hello Bye", multiple=True)
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
    args = setup_base("--a 10 20 --b 3 --c Hello Bye", multiple=True)
    with pytest.raises(InconsistentArgumentError):
        b_s = Base.from_args_multiple(args, 3)

def get_help_text_for(some_class, multiple=False):
    import contextlib
    from io import StringIO
    f = StringIO()
    with contextlib.suppress(SystemExit), contextlib.redirect_stdout(f):
        parser = argparse.ArgumentParser()
        some_class.add_arguments(parser, multiple=multiple)
        args = parser.parse_args(["--help"])
    s = f.getvalue()
    return s

def test_help_displays_class_docstring_text():
    assert Base.__doc__ in get_help_text_for(Base)


def show_help(some_class):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    some_class.add_arguments(parser, multiple=False)
    args = parser.parse_args("--help".split())


if __name__ == "__main__":
    show_help(Extended)
    