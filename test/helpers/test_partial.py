import functools
from collections.abc import Hashable
from dataclasses import dataclass, fields, is_dataclass

import simple_parsing as sp
from simple_parsing import ArgumentParser
from simple_parsing.helpers.partial import Partial

from ..testutils import TestSetup


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
    assert foo_factory.a == 456
    assert foo_factory.b == 2
    assert str(foo_factory) == "FooConfig(a=456, b=2)"

    foo = foo_factory()
    assert foo == Foo(a=456, b=2)
    assert is_dataclass(foo_factory)
    assert isinstance(foo_factory, functools.partial)


def test_partial_function_attribute():
    @dataclass
    class Bob(TestSetup):
        some_fn: Partial[some_function]  # type: ignore

    bob = Bob.setup("--v2 781")
    assert str(bob.some_fn) == "some_function_config(v1=123, v2=781)"
    assert bob.some_fn() == some_function(v2=781)
    assert bob.some_fn(v1=3, v2=7) == some_function(3, 7)


def test_dynamic_classes_are_cached():
    assert Partial[Foo] is Partial[Foo]


def test_pickling():
    # TODO: Test that we can pickle / unpickle these dynamic classes objects.

    import pickle

    dynamic_class = Partial[some_function]

    serialized = pickle.dumps(dynamic_class)

    deserialized = pickle.loads(serialized)
    assert deserialized is dynamic_class


def some_function_with_required_arg(required_arg, v1: int = 123, v2: int = 456):
    """Gives back the mean of two numbers."""
    return required_arg, (v1 + v2) / 2


@dataclass
class FooWithRequiredArg(TestSetup):
    some_fn: Partial[some_function_with_required_arg]


def test_partial_for_fn_with_required_args():
    bob = FooWithRequiredArg.setup("--v1 1 --v2 2")
    assert is_dataclass(bob.some_fn)
    assert isinstance(bob.some_fn, functools.partial)

    assert "required_arg" not in [f.name for f in fields(bob.some_fn)]
    assert bob.some_fn(123) == (123, 1.5)


def test_getattr():
    bob = FooWithRequiredArg.setup("--v1 1 --v2 2")
    some_fn_partial = bob.some_fn
    assert some_fn_partial.v1 == 1
    assert some_fn_partial.v2 == 2


def test_works_with_frozen_instances_as_default():
    @dataclass
    class A:
        x: int
        y: bool = True

    AConfig = sp.config_for(A, ignore_args="x", frozen=True)

    a1_config = AConfig(y=False)
    a2_config = AConfig(y=True)

    assert isinstance(a1_config, functools.partial)
    assert isinstance(a1_config, Hashable)

    @dataclass(frozen=True)
    class ParentConfig:
        a: Partial[A] = sp.subgroups(
            {
                "a1": a1_config,
                "a2": a2_config,
            },
            default=a2_config,
        )

    b = sp.parse(ParentConfig, args="--a a2")
    assert b.a(x=1) == A(x=1, y=a2_config.y)
