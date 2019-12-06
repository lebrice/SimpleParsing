import argparse
import dataclasses
import shlex
from dataclasses import dataclass, field
from typing import *

import pytest

from .testutils import *
from simple_parsing import utils

@dataclass
class SomeDataclass:
    x: float = 123


@parametrize("t", [
    Tuple[int, ...],
    Tuple[str],
    Tuple,
    tuple,
])
def test_is_tuple(t: Type):
    assert utils.is_tuple(t)
    assert not utils.is_list(t)

@parametrize("t", [
    List[int],
    List[str],
    List,
    list,
    List[SomeDataclass],
])
def test_is_list(t: Type):
    assert utils.is_list(t)
    assert not utils.is_tuple(t)

@parametrize("t", [
    List[SomeDataclass],
    Tuple[SomeDataclass],
])
def test_is_list_of_dataclasses(t: Type):
    assert utils.is_tuple_or_list_of_dataclasses(t)

import enum
class Color(enum.Enum):
    RED = "RED"
    ORANGE = "ORANGE"
    BLUE = "BLUE"

class Temperature(enum.IntEnum):
    HOT = 1
    WARM = 0
    COLD = -1
    MONTREAL = -35

@parametrize("t", [
    Color,
    Temperature,
])
def test_is_enum(t: Type):
    assert utils.is_enum(t)