from __future__ import annotations

import pickle
from dataclasses import dataclass, is_dataclass
from test.testutils import TestSetup

from simple_parsing import ArgumentParser
from simple_parsing.helpers.partial import Partial


@dataclass
class Foo:
    a: int = 1
    b: int = 2


def some_function(v1: int = 123, v2: int = 456):
    """Gives back the mean of two numbers."""
    return (v1 + v2) / 2


def test_partial_class_attribute():
    @dataclass
    class Bob(TestSetup):
        foo_factory: Partial[Foo]

    parser = ArgumentParser()
    parser.add_arguments(Bob, dest="bob")
    args = parser.parse_args("--a 456".split())
    bob = args.bob
    foo_factory: Partial[Foo] = bob.foo_factory
    assert is_dataclass(foo_factory)
    assert foo_factory.a == 456
    assert foo_factory.b == 2
    assert str(foo_factory) == "FooConfig(a=456, b=2)"


def test_partial_function_attribute():
    @dataclass
    class Bob(TestSetup):
        some_fn: Partial[some_function]

    bob = Bob.setup("--v2 781")
    assert str(bob.some_fn) == "some_function_config(v1=123, v2=781)"
    assert bob.some_fn() == some_function(v2=781)
    assert bob.some_fn(v1=3, v2=7) == some_function(3, 7)


def test_dynamic_classes_are_cached():
    assert Partial[Foo] is Partial[Foo]


# bob = Bob(foo_factory=Foo, some_fn=some_function)


def test_pickling():
    # TODO: Test that we can pickle / unpickle these dynamic classes objects.
    dynamic_class = Partial[some_function]

    serialized = pickle.dumps(dynamic_class)

    deserialized = pickle.loads(serialized)
    assert deserialized is dynamic_class
