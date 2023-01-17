from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pytest

from simple_parsing import replace, subgroups
from simple_parsing.utils import unflatten_split

from .test_utils import TestSetup

logger = logging.getLogger(__name__)


@dataclass
class A(TestSetup):
    a: float = 0.0


@dataclass
class B(TestSetup):
    b: str = "bar"
    b_post_init: str = field(init=False)

    def __post_init__(self):
        self.b_post_init = self.b + '_post'


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
    nested: NestedDataclasses = field(default_factory=NestedDataclasses)


@pytest.mark.parametrize(
    ("config_cls", "args", "changes"),
    [
        (A, "--a 2.0", {"a": 2.0}),
        pytest.param(
            A, "--b 1.0", {"b": 1.0}, marks=pytest.mark.xfail(reason="Unrecognized arguments")
        ),
        (B, "--b test", {"b": "test"}),
        (AB, "--a_or_b a", {"a_or_b": "a"}),
        (AB, "--a_or_b b --b foo",
         {"__subgroups__@a_or_b": "b", "a_or_b": {'b': 'foo'}}),
        (AB, "--integer_in_string 2", {"integer_in_string": "2"}),
        pytest.param(
            AB,
            "--integer_in_string 2",
            {"integer_in_string": "2", "integer_only_by_post_init": 2},
            marks=pytest.mark.xfail(
                reason="Any field with init=False will raise ValueError"),
        ),
        (CD, "", {}),
        pytest.param(
            lambda: "str_obj",
            "",
            {},
            marks=pytest.mark.xfail(
                reason="Raise TypeError if obj is not dataclass instances"),
        ),
        (
            OuterDataclass,
            "--nested_arg nested_arg_2 --arg1 1 --arg2 2.0",
            {"nested": {"nested_arg": "nested_arg_2", "arg1": 1, "arg2": 2.0}},
        ),
    ],
)
def test_replace_nested_dict(config_cls: type, args: str, changes: dict):
    config = config_cls()
    config_replaced = replace(config, changes)
    logger.info(config_replaced)
    logger.info(config.setup(args))
    assert config.setup(args) == config_replaced
    assert id(config) != id(config_replaced)


@pytest.mark.parametrize(
    ("config_cls", "args", "changes"),
    [
        (CD, "--c_or_d d --d 1", {"__subgroups__@c_or_d": "d", "c_or_d.d": 1}),
        (CD, "--c_or_d c --c True",
         {"__subgroups__@c_or_d": "c", "c_or_d.c": True}),
        (
            OuterDataclass,
            "--some_arg some_arg_1 --nested_arg nested_arg_1",
            {"some_arg": "some_arg_1", "nested.nested_arg": "nested_arg_1"},
        ),
    ],
)
def test_replace_flatten_dict(config_cls: type, args: str, changes: dict):
    config = config_cls()
    config_replaced = replace(config, changes)
    assert config.setup(args) == config_replaced
    assert id(config) != id(config_replaced)


@dataclass
class InnerClass:
    arg1: int = 0
    arg2: str = "foo"


@dataclass(frozen=True)
class OuterClass:
    outarg: int = 1
    nested: InnerClass = field(default_factory=InnerClass)


def test_replace_outerdataclass():
    changes_1 = {"outarg": 2, "nested.arg1": 1, "nested.arg2": "bar"}
    changes_2 = {"outarg": 2, "nested": {"arg1": 1, "arg2": "bar"}}
    c = OuterClass()
    c1 = replace(c, changes_1)
    c2 = replace(c, changes_2)
    assert c1 == c2
    assert id(c1) != id(c2)


def test_replace_nested_1():
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

    config = CD.setup('--c_or_d c')
    assert replace(config, {"c_or_d": {'c': True}}).c_or_d.c == True

    config = CD.setup('--c_or_d d')
    assert replace(config, {"c_or_d": {'d': 2}}).c_or_d.d == 2

    config = CD.setup('--c_or_d d')
    assert replace(config, {"c_or_d": D(d=2)}).c_or_d.d == 2

    config = CD.setup('--c_or_d d')
    assert replace(config, {"c_or_d": 'd'}).c_or_d.d == 0


@dataclass
class Config(TestSetup):
    ab_or_cd: AB | CD = subgroups(
        {"ab": AB, "cd": CD},
        default_factory=AB,
    )


@pytest.mark.parametrize(
    ("config_cls", "args", "changes"),
    [
        (Config, "--ab_or_cd cd --c_or_d d",
         {"__subgroups__@ab_or_cd": "cd", "ab_or_cd.__subgroups__@c_or_d": "d"}),
        (Config, "--ab_or_cd cd --c_or_d d",
         {"__subgroups__@ab_or_cd": "cd", "ab_or_cd.c_or_d": "d"}),
        (Config, "--ab_or_cd cd --c_or_d d",
         {"__subgroups__@ab_or_cd": "cd", "ab_or_cd": {"__subgroups__@c_or_d": "d"}}),
        (Config, "--ab_or_cd cd --c_or_d d",
         {"__subgroups__@ab_or_cd": "cd", "ab_or_cd": {"c_or_d": "d"}}),
    ],
)
def test_replace_nested_subgroups(config_cls: type, args: str, changes: dict):
    config = config_cls()
    print(config.setup(args))
    config_replaced = replace(config, changes)
    print(config_replaced)
    assert config.setup(args) == config_replaced
    assert id(config) != id(config_replaced)


@dataclass
class A:
    a: int = 0

@dataclass
class B:
    b: str = "b"

@dataclass
class Config:
    a_or_b: A | B = field(default_factory=A)
    
def test_example_in_docstring():
    config = Config(a_or_b=A(a=1))
    assert replace(config, {"a_or_b": {"a": 2}}) == Config(a_or_b=A(a=2))
    assert replace(config, {"a_or_b.a": 2}) == Config(a_or_b=A(a=2))
    assert replace(config, {"a_or_b": B(b="bob")}) == Config(a_or_b=B(b='bob'))
