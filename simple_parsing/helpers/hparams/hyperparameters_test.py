from dataclasses import dataclass
from typing import Sequence, Union

import pytest

from .hparam import categorical, log_uniform, uniform
from .hyperparameters import HyperParameters

numpy_installed = False
try:
    import numpy as np

    numpy_installed = True
except ImportError:
    pass


@dataclass
class A(HyperParameters):
    learning_rate: float = uniform(0.0, 1.0)


@dataclass
class B(A):
    momentum: float = uniform(0.0, 1.0)


@pytest.mark.skipif(not numpy_installed, reason="Test requires numpy.")
def test_to_array():
    b: B = B.sample()
    array = b.to_array()
    assert np.isclose(array[0], b.learning_rate)
    assert np.isclose(array[1], b.momentum)


@pytest.mark.skipif(not numpy_installed, reason="Test requires numpy.")
def test_from_array():
    array = np.arange(2)
    b: B = B.from_array(array)
    assert b.learning_rate == 0.0
    assert b.momentum == 1.0


@dataclass
class C(HyperParameters):
    lr: float = uniform(0.0, 1.0)
    momentum: float = uniform(0.0, 1.0)


def test_clip_within_bounds():
    """Test to make sure that the `clip_within_bounds` actually restricts the values of the
    HyperParameters to be within the bounds."""
    # valid range for learning_rate is (0 - 1].
    a = A(learning_rate=123)
    assert a.learning_rate == 123
    a = a.clip_within_bounds()
    assert a.learning_rate == 1.0

    b = B(learning_rate=0.5, momentum=456)
    assert b.clip_within_bounds() == B(learning_rate=0.5, momentum=1)

    # Test that the types are maintained.
    @dataclass
    class C(HyperParameters):
        a: int = uniform(123, 456, discrete=True)
        b: float = log_uniform(4.56, 123.456)
        c: str = categorical("foo", "bar", "baz")

    with pytest.raises(TypeError):
        _ = C()

    with pytest.raises(TypeError):
        _ = C(a=123)

    with pytest.raises(TypeError):
        _ = C(b=4.56)

    with pytest.raises(TypeError):
        _ = C(c="bar")

    # TODO: IDEA: how about we actually do some post-processing to always clip stuff
    # between bounds?
    # Check that it doesn't change anything if the values are within the range.
    assert C(a=1000, b=1.23, c="bar").clip_within_bounds() == C(456, 4.56, "bar")
    assert C(a=-1.234, b=1000, c="foo").clip_within_bounds() == C(123, 123.456, "foo")


def test_strict_bounds():
    """When creating a class and using a hparam field with `strict=True`, the values will be
    restricted to be within the given bounds."""

    @dataclass
    class C(HyperParameters):
        a: int = uniform(0, 1, strict=True)
        b: float = log_uniform(4.56, 123.456)
        c: str = categorical("foo", "bar", "baz", default="foo", strict=True)

    # valid range for a is [0, 1).
    with pytest.raises(
        ValueError,
        match="Field 'a' got value 123, which is outside of the defined prior",
    ):
        _ = C(a=123, b=10, c="foo")

    with pytest.raises(
        ValueError,
        match="Field 'c' got value 'yolo', which is outside of the defined prior",
    ):
        _ = C(a=0.5, b=0.1, c="yolo")

    # should NOT raise an error, since the field `b` isn't strict.
    _ = C(a=0.1, b=-1.26, c="bar")


def test_nesting():
    @dataclass
    class Child(HyperParameters):
        foo: int = uniform(0, 10, default=5)

    from simple_parsing import mutable_field

    @dataclass
    class Parent(HyperParameters):
        child_a: Child = mutable_field(Child, foo=3)

    parent = Parent.sample()
    assert isinstance(parent, Parent)
    assert isinstance(parent.child_a, Child)


def test_choice_field():
    @dataclass
    class Child(HyperParameters):
        hparam: float = categorical(
            {
                "a": 1.23,
                "b": 4.56,
                "c": 7.89,
            },
            default=1.23,
        )

    bob = Child()
    assert bob.hparam == 1.23

    bob = Child.sample()
    assert bob.hparam in {1.23, 4.56, 7.89}
    assert Child.get_orion_space_dict() == {
        "hparam": "choices(['a', 'b', 'c'], default_value='a')"
    }


def test_choice_field_with_values_of_a_weird_type():
    @dataclass
    class Bob(HyperParameters):
        hparam_type: float = categorical(
            {
                "a": A,
                "b": B,
                "c": C,
            },
            probabilities={
                "a": 0.1,
                "b": 0.2,
                "c": 0.7,
            },
            default=B,
        )

    bob = Bob()
    assert bob.hparam_type == B

    bob = Bob.sample()
    assert bob.hparam_type in {A, B, C}
    assert Bob.get_orion_space_dict() == {
        "hparam_type": "choices({'a': 0.1, 'b': 0.2, 'c': 0.7}, default_value='b')"
    }


@pytest.mark.xfail(
    reason="TODO: it isn't trivial how to fix this, without having to rework the "
    "from_dict from simple-parsing."
)
def test_replace_int_or_float_preserves_type():
    @dataclass
    class A(HyperParameters):
        # How much of training dataset to check (floats = percent, int = num_batches)
        limit_train_batches: Union[int, float] = 1.0
        # How much of validation dataset to check (floats = percent, int = num_batches)
        limit_val_batches: Union[int, float] = 1.0
        # How much of test dataset to check (floats = percent, int = num_batches)
        limit_test_batches: Union[int, float] = 1.0

    a = A()
    assert isinstance(a.limit_test_batches, float)
    b = a.replace(limit_train_batches=0.5)
    assert isinstance(b.limit_test_batches, float)


try:
    from orion.core.io.space_builder import SpaceBuilder

    orion_installed = True
except ImportError:
    orion_installed = False


@dataclass
class Foo(HyperParameters):
    x: Sequence[int] = uniform(0, 10, default=(5, 5), shape=2)
    y: Sequence[int] = uniform(0, 10, default=(5, 5, 5), shape=3)
    z: Sequence[int] = uniform(0, 10, default=2, shape=5)


def test_priors_with_shape():
    foo = Foo()
    assert foo.x == (5, 5)
    assert foo.y == (5, 5, 5)
    assert foo.z == (2, 2, 2, 2, 2)

    foo = Foo.sample()
    assert len(foo.x) == 2
    assert len(foo.y) == 3
    assert len(foo.z) == 5


@pytest.mark.xfail(reason="Need to update this since spaces give Trials, not points.")
@pytest.mark.skipif(not numpy_installed, reason="Test requires numpy.")
@pytest.mark.skipif(not orion_installed, reason="Test requires Orion.")
def test_contains():
    # TODO: Add a convenience method for creating a Space object from Orion directly.
    foo = Foo(x=(2, 3), y=(1, 2, 3), z=(1, 2, 3, 4, 5))
    space_builder = SpaceBuilder()
    space_config = Foo.get_orion_space_dict()
    space = space_builder.build(space_config)
    assert foo.to_array() in space


def test_field_types():
    @dataclass
    class C(HyperParameters):
        a: int = uniform(123, 456)
        b: float = uniform(4.56, 123.456, default=123)
        c: float = uniform(4.56, 123.456, default=10, discrete=True)
        d: float = uniform(4.56, 123.456, default=10, discrete=False)
        e: float = uniform(4.56, 123.456, default=10, discrete=False, shape=2)
        f: float = uniform(10, 100, default=20, shape=2)

    cs = [C.sample() for _ in range(100)]
    assert C.get_priors()["a"].discrete is True
    assert all(isinstance(c.a, int) for c in cs)

    assert C.get_priors()["b"].discrete is False
    assert all(isinstance(c.b, float) for c in cs)

    assert C.get_priors()["c"].discrete is True
    assert all(isinstance(c.c, int) for c in cs)

    assert C.get_priors()["d"].discrete is False
    assert all(isinstance(c.d, float) for c in cs)

    assert C.get_priors()["e"].discrete is False
    assert all(all(isinstance(v, float) for v in c.e) for c in cs)
    assert C.get_priors()["f"].discrete is True

    if numpy_installed:
        assert all(c.f.dtype == int for c in cs)
    else:
        assert all(all(isinstance(v, int) for v in c.f) for c in cs)
