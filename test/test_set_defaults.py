""" Tests for the setdefaults method of the parser. """
from dataclasses import dataclass

from simple_parsing.parsing import ArgumentParser

from .testutils import TestSetup


@dataclass
class Foo(TestSetup):
    a: int = 123
    b: str = "hello"


def test_set_defaults():
    parser = ArgumentParser()
    parser.add_arguments(Foo, dest="foo")
    parser.set_defaults(foo=Foo(b="HOLA"))
    args = parser.parse_args("")
    assert args.foo == Foo(b="HOLA")
