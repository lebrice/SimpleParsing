from dataclasses import dataclass
from typing import Union

import numpy as np
import pytest

from .hyperparameters import HyperParameters, hparam, log_uniform, uniform


@dataclass
class A(HyperParameters):
    learning_rate: float = uniform(0.0, 1.0)


@dataclass
class B(A):
    momentum: float = uniform(0.0, 1.0)


@dataclass
class C(HyperParameters):
    lr: float = uniform(0.0, 1.0)
    momentum: float = uniform(0.0, 1.0)


def test_to_array():
    b: B = B.sample()
    array = b.to_array()
    assert np.isclose(array[0], b.learning_rate)
    assert np.isclose(array[1], b.momentum)


def test_from_array():
    array = np.arange(2)
    b: B = B.from_array(array)
    assert b.learning_rate == 0.0
    assert b.momentum == 1.0


def test_distance_between_same_object():
    x1 = A(learning_rate=1.2)
    assert x1.distance_to(x1) == 0


def test_distance_between_same_type():
    x1 = A(learning_rate=0.0)
    x2 = A(learning_rate=1.0)
    assert x1.distance_to(x2) == 1.0


def test_distance_between_same_type_with_weights():
    x1 = A(learning_rate=0)
    x2 = A(learning_rate=0.8)
    weights = {"learning_rate": 0.5}
    assert x1.distance_to(x2, weights=weights) == 0.4
    assert x2.distance_to(x1, weights=weights) == 0.4


def test_distance_between_different_types():
    x1 = A(learning_rate=0.0)
    x2 = B(learning_rate=0.5, momentum=0.2)
    assert x1.distance_to(x2) == 0.5
    assert x2.distance_to(x1) == 0.5


def test_distance_between_different_types_with_weights():
    x1 = A(learning_rate=0.0)
    x2 = B(learning_rate=0.5, momentum=0.2)
    weights = {"learning_rate": 0.2}
    assert x1.distance_to(x2, weights=weights) == 0.1
    assert x2.distance_to(x1, weights=weights) == 0.1


@pytest.mark.xfail(reason="not using the 'translator' feature here atm.")
def test_distance_between_different_type_with_equivalent_names():
    x1 = A(learning_rate=0.0)
    x2 = C(lr=2.0)
    assert x1.distance_to(x2) == 2.0

    x1 = B(learning_rate=0.0, momentum=1)
    x2 = C(lr=1, momentum=0.5)

    assert x2.distance_to(x1) == 1.5
    assert x1.distance_to(x2) == 1.5


@pytest.mark.xfail(reason="not using the 'translator' feature here atm.")
def test_distance_between_different_types_with_equivalent_names_with_weights():
    x1 = A(learning_rate=0.0)
    x2 = C(lr=2.0)
    weights = dict(learning_rate=0.5)
    assert x1.distance_to(x2, weights=weights) == 1.0
    assert x2.distance_to(x1, weights=weights, translate=True) == 1.0


@pytest.mark.xfail(reason="not using the 'translator' feature here atm.")
def test_distance_between_different_types_and_equivalent_names():
    x1 = A(learning_rate=0.0)
    x2 = C(lr=0.6, momentum=0.2)
    assert x1.distance_to(x2) == 0.6
    assert x2.distance_to(x1) == 0.6


def test_clip_within_bounds():
    """Test to make sure that the `clip_within_bounds` actually restricts the
    values of the HyperParameters to be within the bounds.
    """
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

    # Check that it doesn't change anything if the values are within the range.
    assert C().clip_within_bounds() == C()

    assert C(a=-1.234, b=10).clip_within_bounds() == C(a=123, b=10)


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


from typing import Type

from .hparam import categorical


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
