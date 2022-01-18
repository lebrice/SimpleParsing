import collections
from simple_parsing.helpers.hparams import uniform
from typing import Union
from simple_parsing.helpers.fields import field, subparsers
from simple_parsing.helpers.hparams.hyperparameters import HyperParameters
from dataclasses import dataclass
from .testutils import TestSetup
import functools

from simple_parsing import ArgumentParser


@dataclass
class A:
    foo: int = 123


@dataclass
class B:
    bar: float = 4.56


class TestWithDefault:
    @dataclass
    class Options(TestSetup):
        config: Union[A, B] = subparsers({"a": A, "b": B}, default=A(foo=0))

    def test_default_is_used_when_no_args_passed(self):
        assert self.Options.setup("").config == A(foo=0)

    def test_subparsers_work(self):
        assert self.Options.setup("a --foo 456").config == A(foo=456)
        assert self.Options.setup("b --bar 1.23").config == B(bar=1.23)


class TestWithDefaultFactory:
    @dataclass
    class Options(TestSetup):
        config: Union[A, B] = subparsers(
            {"a": A, "b": B}, default_factory=functools.partial(A, foo=0)
        )

    def test_default_is_used_when_no_args_passed(self):
        assert self.Options.setup("").config == A(foo=0)

    def test_subparsers_work(self):
        assert self.Options.setup("a --foo 456").config == A(foo=456)
        assert self.Options.setup("b --bar 1.23").config == B(bar=1.23)


class TestWithoutSubparsersField:
    @dataclass
    class Options(TestSetup):
        config: Union[A, B] = field(default_factory=functools.partial(A, foo=0))

    def test_default_is_used_when_no_args_passed(self):
        assert self.Options.setup("").config == A(foo=0)

    def test_subparsers_work(self):
        assert self.Options.setup("a --foo 456").config == A(foo=456)
        assert self.Options.setup("b --bar 1.23").config == B(bar=1.23)


class TestWithoutSubparsersField:
    @dataclass
    class Options(TestSetup):
        config: Union[A, B] = field(
            default=A(foo=0),
        )

    def test_default_is_used_when_no_args_passed(self):
        assert self.Options.setup("").config == A(foo=0)

    def test_subparsers_work(self):
        assert self.Options.setup("a --foo 456").config == A(foo=456)
        assert self.Options.setup("b --bar 1.23").config == B(bar=1.23)


def test_nesting_of_optional_subparsers():
    @dataclass
    class Bob:
        config: Union[A, B] = subparsers({"a": A, "b": B}, default=A(foo=0))

    @dataclass
    class Clarice:
        config: Union[A, B] = subparsers({"a": A, "b": B}, default=A(foo=0))

    @dataclass
    class NestedOptions(TestSetup):
        friend: Union[Bob, Clarice] = Bob()

    assert NestedOptions.setup("") == NestedOptions()
    assert NestedOptions.setup("bob") == NestedOptions(friend=Bob())
    assert NestedOptions.setup("bob a") == NestedOptions(friend=Bob(config=A()))
    assert NestedOptions.setup("bob a --foo 1") == NestedOptions(friend=Bob(config=A(foo=1)))
    assert NestedOptions.setup("bob b") == NestedOptions(friend=Bob(config=B()))
    assert NestedOptions.setup("bob b --bar 0.") == NestedOptions(friend=Bob(config=B(bar=0.0)))
    assert NestedOptions.setup("clarice") == NestedOptions(friend=Clarice())
    assert NestedOptions.setup("clarice a") == NestedOptions(friend=Clarice(config=A()))
    assert NestedOptions.setup("clarice a --foo 1") == NestedOptions(
        friend=Clarice(config=A(foo=1))
    )
    assert NestedOptions.setup("clarice b") == NestedOptions(friend=Clarice(config=B()))
    assert NestedOptions.setup("clarice b --bar 0.") == NestedOptions(
        friend=Clarice(config=B(bar=0.0))
    )


class ModelA(HyperParameters):
    foo: float = uniform(0, 1, default=0.5)


class ModelB(HyperParameters):
    bar: int = uniform(0, 10, default=5, discrete=True)


@dataclass
class Options(HyperParameters):
    model: Union[ModelA, ModelB] = field(default_factory=ModelA)


import pytest

import random


@pytest.mark.parametrize("seed", [123, 456, 789])
def test_sample_with_subparsers_field(seed: int):

    random.seed(seed)

    samples = [Options.sample() for _ in range(10)]
    assert not all(sample == Options() for sample in samples), samples

    model_types = [type(Options.sample().model) for _ in range(100)]
    assert len(set(model_types)) == 2
    assert 40 <= collections.Counter(model_types)[ModelA] <= 60
