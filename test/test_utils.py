import enum
import os
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Type

import simple_parsing.utils as utils
from simple_parsing import mutable_field
from simple_parsing.helpers import dict_field, list_field, set_field
from simple_parsing.utils import flatten_join, unflatten_split

from .testutils import TestSetup, parametrize


@dataclass
class SomeDataclass:
    x: float = 123


@parametrize(
    "t",
    [
        Tuple[int, ...],
        Tuple[str],
        Tuple,
        tuple,
    ],
)
def test_is_tuple(t: Type):
    assert utils.is_tuple(t)
    assert not utils.is_list(t)


@parametrize(
    "t",
    [
        List[int],
        List[str],
        List,
        list,
        List[SomeDataclass],
    ],
)
def test_is_list(t: Type):
    assert utils.is_list(t)
    assert not utils.is_tuple(t)


@parametrize(
    "t",
    [
        List[SomeDataclass],
        Tuple[SomeDataclass],
    ],
)
def test_is_list_of_dataclasses(t: Type):
    assert utils.is_tuple_or_list_of_dataclasses(t)


@dataclass
class A:
    a: str = "bob"


@dataclass
class B:
    # # shared_list: List = [] # not allowed.
    # different_list: List = field(default_factory=list)
    shared: A = A()
    different: A = mutable_field(A, a="123")


def test_mutable_field():
    b1 = B()
    b2 = B()

    assert id(b1.shared) == id(b2.shared), f"{b1.shared} should have the same id as {b2.shared}"
    assert id(b1.different) != id(b2.different), f"{b1.different} has the same id."


class Color(enum.Enum):
    RED = "RED"
    ORANGE = "ORANGE"
    BLUE = "BLUE"


class Temperature(enum.IntEnum):
    HOT = 1
    WARM = 0
    COLD = -1
    MONTREAL = -35


@parametrize(
    "t",
    [
        Color,
        Temperature,
    ],
)
def test_is_enum(t: Type):
    assert utils.is_enum(t)


def test_json_serializable(tmpdir):
    from .nesting.example_use_cases import HyperParameters

    hparams = HyperParameters()

    filename = "hparams.json"
    hparams.save_json(os.path.join(tmpdir, filename))
    hparams_ = HyperParameters.load_json(os.path.join(tmpdir, filename))
    assert hparams == hparams_


def test_list_field():
    @dataclass
    class A:
        a: List[str] = list_field("bob", "john", "bart")

    a1 = A()
    a2 = A()
    assert id(a1.a) != id(a2.a)


def test_set_field():
    @dataclass
    class A:
        a: Set[str] = set_field("bob", "john", "bart")

    a1 = A()
    a2 = A()
    assert id(a1.a) != id(a2.a)


def test_dict_field():
    default = {"bob": 0, "john": 1, "bart": 2}

    @dataclass
    class A:
        a: Dict[str, int] = dict_field(default)

    a1 = A()
    print(a1.a)
    assert a1.a == default
    a2 = A()
    assert id(a1.a) != id(a2.a)


def test_dict_field_with_keyword_args():
    default = {"bob": 0, "john": 1, "bart": 2}

    @dataclass
    class A(TestSetup):
        a: Dict[str, int] = dict_field(dict(bob=0, john=1, bart=2))

    a1 = A()
    a2 = A()
    assert a1.a == a2.a == default
    assert id(a1.a) != id(a2.a)


def test_dict_field_without_args():
    default = {}

    @dataclass
    class A(TestSetup):
        a: Dict[str, int] = dict_field()

    a1 = A()
    a2 = A()
    assert a1.a == a2.a == default
    assert id(a1.a) != id(a2.a)


def test_flatten():
    """Test basic functionality of flatten"""
    d = {"a": {"b": 2, "c": 3}, "c": {"d": 3, "e": 4}}
    assert flatten_join(d) == {"a.b": 2, "a.c": 3, "c.d": 3, "c.e": 4}


def test_flatten_double_ref():
    """Test proper handling of double references in dicts"""
    a = {"b": 2, "c": 3}
    d = {"a": a, "d": {"e": a}}
    assert flatten_join(d) == {"a.b": 2, "a.c": 3, "d.e.b": 2, "d.e.c": 3}


def test_unflatten():
    """Test than unflatten(flatten(x)) is idempotent"""
    a = {"b": 2, "c": 3}
    d = {"a": a, "d": {"e": a}}
    assert unflatten_split(flatten_join(d)) == d
