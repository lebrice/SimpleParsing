import sys
from dataclasses import dataclass
from typing import Union

import pytest

from simple_parsing import subgroups

from .testutils import TestSetup


@dataclass
class Foo:
    a: int = 1
    b: int = 2


@dataclass
class Bar:
    c: int = 1
    d: int = 2


@pytest.mark.xfail()
def test_default_factory_subgroups_1():
    @dataclass
    class Bob(TestSetup):
        thing: Union[Foo, Bar] = subgroups({"foo_thing": Foo, "bar_thing": Bar})

    assert "--thing.c" in Bob.get_help_text("--help")

    assert "--thing.a" in Bob.get_help_text("--thing foo_thing --help")
    assert "--thing.c" in Bob.get_help_text("--thing bar_thing --help")


def test_default_factory_subgroups_2():
    @dataclass
    class Bob(TestSetup):
        thing: Union[Foo, Bar] = subgroups(
            {"foo_thing": Foo, "bar_thing": Bar}, default_factory=lambda: Bar(d=3)
        )

    assert "--thing.c" in Bob.get_help_text("--help")

    assert "--thing.a" in Bob.get_help_text("--thing foo_thing --help")
    assert "--thing.c" in Bob.get_help_text("--thing bar_thing --help")


@pytest.mark.skipif(
    sys.version_info >= (3, 11),
    reason="Mutable Default Error break this test case for Python >= 3.11",
)
def test_default_factory_subgroups_3():
    @dataclass
    class Bob(TestSetup):
        thing: Union[Foo, Bar] = subgroups({"foo_thing": Foo, "bar_thing": Bar}, default=Bar(d=3))

    assert "--thing.c" in Bob.get_help_text("--help")

    assert "--thing.a" in Bob.get_help_text("--thing foo_thing --help")
    assert "--thing.c" in Bob.get_help_text("--thing bar_thing --help")


@pytest.mark.skipif(
    sys.version_info >= (3, 11),
    reason="Mutable Default Error break this test case for Python >= 3.11",
)
def test_default_factory_subgroups_4():
    @dataclass
    class Bob(TestSetup):
        thing: Union[Foo, Bar] = subgroups({"foo_thing": Foo, "bar_thing": Bar}, default=Bar)

    assert "--thing.c" in Bob.get_help_text("--help")

    assert "--thing.a" in Bob.get_help_text("--thing foo_thing --help")
    assert "--thing.c" in Bob.get_help_text("--thing bar_thing --help")
