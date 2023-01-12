from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

import pytest

import simple_parsing as sp
from simple_parsing import ArgumentGenerationMode, parse, subgroups

from .test_utils import TestSetup


@dataclass
class A(TestSetup):
    a: float = 0.0


@dataclass
class B(TestSetup):
    b: str = "bar"


@dataclass
class AB(TestSetup):
    integer_only_by_post_init: int = field(init=False)
    integer_in_string: str = "1"
    a_or_b: A | B = subgroups({"a": A, "b": B}, default="a")

    def __post_init__(self):
        self.integer_only_by_post_init = int(self.integer_in_string)


@dataclass
class C:
    c: bool = False


@dataclass
class D:
    d: int = 0


@dataclass(frozen=True)
class CD(TestSetup):
    c_or_d: C | D = subgroups({"c": C, "d": D}, default="c")

    other_arg: str = "bob"


@pytest.mark.parametrize(
    ("config_cls", "args", "changes"),
    [
        (A, "--a 2.0", {"a": 2.0}),
        pytest.param(
            A, "--b 1.0", {"b": 1.0}, marks=pytest.mark.xfail(reason="Unrecognized arguments")
        ),
        (B, "--b test", {"b": "test"}),
        (AB, "--a_or_b a", {"a_or_b": "a"}),
        (AB, "--integer_in_string 2", {"integer_in_string": "2"}),
        pytest.param(
            AB,
            "--integer_in_string 2",
            {"integer_in_string": "2", "integer_only_by_post_init": 2},
            marks=pytest.mark.xfail(reason="Any field with init=False will raise ValueError"),
        ),
        (CD, "", {}),
        (CD, "--c_or_d d --d 1", {"c_or_d": "d", "c_or_d.d": 1}),
        (CD, "--c_or_d c --c True", {"c_or_d": "c", "c_or_d.c": True}),
        pytest.param(
            lambda: "str_obj",
            "",
            {},
            marks=pytest.mark.xfail(reason="Raise TypeError if obj is not dataclass instances"),
        ),
    ],
)
def test_replace_nested_dataclasses(config_cls: type, args: str, changes: Dict[str, Any]):
    config = config_cls()
    config_replaced = sp.replace(config, changes)
    assert config.setup(args) == config_replaced
    assert id(config) != id(config_replaced)
