""" Tests for compatibility with the postponed evaluation of annotations. """
from __future__ import annotations
import dataclasses

from simple_parsing import ArgumentParser
import sys
import pytest
from .testutils import TestSetup
from dataclasses import fields

from dataclasses import dataclass, field
from .testutils import TestSetup


@dataclass
class Foo(TestSetup):
    a: int = 123

    b: str = "fooobar"
    c: tuple[int, float] = (123, 4.56)

    d: list[bool] = field(default_factory=list)


@dataclass
class Bar(TestSetup):
    barry: Foo = field(default_factory=Foo)
    joe: "Foo" = field(default_factory=lambda: Foo(b="rrrrr"))
    z: float = 123.456
    some_list: list[float] = field(default_factory=[1.0, 2.0].copy)


@pytest.mark.skipif(
    sys.version_info < (3, 7), reason="Needs access to annotations from __future__"
)
def test_future_annotations():
    foo = Foo.setup()
    assert foo == Foo()

    foo = Foo.setup("--a 2 --b heyo --c 1 7.89")
    assert foo == Foo(a=2, b="heyo", c=(1, 7.89))


@pytest.mark.skipif(
    sys.version_info < (3, 7), reason="Needs access to annotations from __future__"
)
def test_future_annotations_nested():
    bar = Bar.setup()
    assert bar == Bar()
    assert bar.barry == Foo()
    bar = Bar.setup("--barry.a 2 --barry.b heyo --barry.c 1 7.89")
    assert bar.barry == Foo(a=2, b="heyo", c=(1, 7.89))
    assert isinstance(bar.joe, Foo)


@dataclass
class ClassWithNewUnionSyntax(TestSetup):
    v: int | float = 123


def test_new_union_syntax():
    assert ClassWithNewUnionSyntax.setup() == ClassWithNewUnionSyntax()
    assert ClassWithNewUnionSyntax.setup("--v 456") == ClassWithNewUnionSyntax(v=456)
    assert ClassWithNewUnionSyntax.setup("--v 4.56") == ClassWithNewUnionSyntax(v=4.56)
    from simple_parsing.utils import is_union

    type_annotation = dataclasses.fields(ClassWithNewUnionSyntax)[0].type
    assert is_union(type_annotation)

    # with pytest.raises(Exception):
    #     assert ClassWithNewUnionSyntax.setup("--v bob")
