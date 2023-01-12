from __future__ import annotations

from dataclasses import dataclass, field

import pytest

import simple_parsing as sp
from simple_parsing import subgroups

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


@dataclass
class NestedDataclasses:
    nested_arg: str = "nested_arg"
    arg1: int = 0
    arg2: float = 0.0


@dataclass
class OuterDataclass(TestSetup):
    some_arg: str = "some_arg"
    nested: NestedDataclasses = NestedDataclasses()


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
        (
            OuterDataclass,
            "--some_arg some_arg_1 --nested_arg nested_arg_1",
            {"some_arg": "some_arg_1", "nested.nested_arg": "nested_arg_1"},
        ),
        (
            OuterDataclass,
            "--nested_arg nested_arg_2 --arg1 1 --arg2 2.0",
            {"nested": {"nested_arg": "nested_arg_2", "arg1": 1, "arg2": 2.0}},
        ),
    ],
)
def test_replace_nested_dataclasses(config_cls: type, args: str, changes: dict):
    config = config_cls()
    config_replaced = sp.replace(config, changes)
    assert config.setup(args) == config_replaced
    assert id(config) != id(config_replaced)


@dataclass
class InnerClass:
    arg1: int = 0
    arg2: str = "foo"


@dataclass(frozen=True)
class OuterClass:
    outarg: int = 1
    nested: InnerClass = InnerClass()


def test_replace_nested_dictionary():
    changes_1 = {"outarg": 2, "nested.arg1": 1, "nested.arg2": "bar"}
    changes_2 = {"outarg": 2, "nested": {"arg1": 1, "arg2": "bar"}}
    c = OuterClass()
    c1 = sp.replace(c, changes_1)
    c2 = sp.replace(c, changes_2)
    assert c1 == c2
    assert id(c1) != id(c2)
