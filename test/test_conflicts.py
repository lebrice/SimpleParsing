"""Tests for weird conflicts."""
import argparse
import functools
from dataclasses import dataclass, field

from simple_parsing import ArgumentParser

from .testutils import TestSetup, raises


def test_arg_and_dataclass_with_same_name(silent):
    @dataclass
    class SomeClass:
        a: int = 1  # some docstring for attribute 'a'

    parser = ArgumentParser()
    parser.add_argument("--a", default=123)
    with raises(argparse.ArgumentError):
        parser.add_arguments(SomeClass, dest="some_class")
        parser.parse_args("")


def test_arg_and_dataclass_with_same_name_after_prefixing(silent):
    @dataclass
    class SomeClass:
        a: int = 1  # some docstring for attribute 'a'

    @dataclass
    class Parent:
        pre: SomeClass = field(default_factory=lambda: SomeClass)
        bla: SomeClass = field(default_factory=lambda: SomeClass)

    parser = ArgumentParser()
    parser.add_argument("--pre.a", default=123, type=int)
    with raises(argparse.ArgumentError):
        parser.add_arguments(Parent, dest="some_class")
        parser.parse_args("--pre.a 123 --pre.a 456".split())


def test_weird_hierarchy():
    @dataclass
    class Base:
        v: float = 0.0

    @dataclass
    class A(Base):
        pass

    @dataclass
    class B(Base):
        pass

    @dataclass
    class C(Base):
        pass

    @dataclass
    class Options:
        a: A = field(default_factory=functools.partial(A, 0.1))
        b: B = field(default_factory=functools.partial(B, 0.2))

    @dataclass
    class Settings(TestSetup):
        opt: Options = field(default_factory=Options)
        c: Base = field(default_factory=functools.partial(C, 0.3))

    opt = Settings.setup("")
    print(opt)


def test_parent_child_conflict():
    @dataclass
    class HParams:
        batch_size: int = 32

    @dataclass
    class Parent2(TestSetup):
        batch_size: int = 48
        child: HParams = field(default_factory=HParams)

    p: Parent2 = Parent2.setup()
    assert p.child.batch_size == 32
    assert p.batch_size == 48
