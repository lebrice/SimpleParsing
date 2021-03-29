import pytest
from .warm_start_hparams import WarmStarteableHParams
from simple_parsing.helpers.hyperparameters import uniform
from dataclasses import dataclass


@dataclass
class A(WarmStarteableHParams):
    learning_rate: float = uniform(0.0, 1.0)


@dataclass
class B(A):
    momentum: float = uniform(0.0, 1.0)


@dataclass
class C(WarmStarteableHParams):
    lr: float = uniform(0.0, 1.0)
    momentum: float = uniform(0.0, 1.0)


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
