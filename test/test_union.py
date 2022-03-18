from dataclasses import dataclass

from simple_parsing.parsing import ParsingError
from .testutils import TestSetup, exits_and_writes_to_stderr, raises
from typing import Union


def test_union_type():
    @dataclass
    class Foo(TestSetup):
        x: Union[int, float, str] = 0

    foo = Foo.setup("--x 1.2")
    assert foo.x == 1.2

    foo = Foo.setup("--x bob")
    assert foo.x == "bob"

    foo = Foo.setup("--x 2")
    assert foo.x == 2 and type(foo.x) is int


def test_union_type_raises_error():
    @dataclass
    class Foo2(TestSetup):
        x: Union[int, float] = 0

    foo = Foo2.setup("--x 1.2")
    assert foo.x == 1.2

    with exits_and_writes_to_stderr(match="invalid int|float value: 'bob'"):
        foo = Foo2.setup("--x bob")

    foo = Foo2.setup("--x 2")
    assert foo.x == 2 and type(foo.x) is int
