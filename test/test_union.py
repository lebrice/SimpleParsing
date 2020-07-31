from dataclasses import dataclass
from .testutils import *
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