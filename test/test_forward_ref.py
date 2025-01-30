from dataclasses import dataclass

from simple_parsing import field

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
    z: "float" = 123.456
    some_list: "list[float]" = field(default_factory=[1.0, 2.0].copy)


def test_forward_ref():
    foo = Foo.setup()
    assert foo == Foo()

    foo = Foo.setup("--a 2 --b heyo --c 1 7.89")
    assert foo == Foo(a=2, b="heyo", c=(1, 7.89))


def test_forward_ref_nested():
    bar = Bar.setup()
    assert bar == Bar()
    assert bar.barry == Foo()
    bar = Bar.setup("--barry.a 2 --barry.b heyo --barry.c 1 7.89")
    assert bar.barry == Foo(a=2, b="heyo", c=(1, 7.89))
    assert isinstance(bar.joe, Foo)
