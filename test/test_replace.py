from __future__ import annotations

import functools
import logging
from dataclasses import dataclass, field

import pytest

from simple_parsing import replace, subgroups

logger = logging.getLogger(__name__)


@dataclass
class A:
    a: float = 0.0


@dataclass
class B:
    b: str = "bar"
    b_post_init: str = field(init=False)

    def __post_init__(self):
        self.b_post_init = self.b + "_post"


@dataclass
class AB:
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


@dataclass
class CD:
    c_or_d: C | D = subgroups({"c": C, "d": D}, default="c")

    other_arg: str = "bob"


@dataclass
class NestedSubgroupsConfig:
    ab_or_cd: AB | CD = subgroups(
        {"ab": AB, "cd": CD},
        default_factory=AB,
    )


@dataclass
class Level1:
    level: int = 1
    name: str = "level1"


@dataclass
class Level2:
    level: int = 2
    name: str = "level2"
    prev: Level1 = field(default_factory=Level1)


@dataclass
class Level3:
    level: int = 3
    name: str = "level3"
    prev: Level2 = field(default_factory=functools.partial(Level2, name="level2_foo"))


@dataclass
class InnerPostInit:
    in_arg: float = 1.0
    in_arg_post: str = field(init=False)
    for_outer_post: str = "foo"

    def __post_init__(self):
        self.in_arg_post = str(self.in_arg)


@dataclass
class OuterPostInit:
    out_arg: int = 1
    out_arg_post: str = field(init=False)
    inner: InnerPostInit = field(default_factory=InnerPostInit)
    arg_post_on_inner: str = field(init=False)

    def __post_init__(self):
        self.out_arg_post = str(self.out_arg)
        self.arg_post_on_inner = self.inner.for_outer_post + "_outer"


@pytest.mark.parametrize(
    ("dest_config", "src_config", "changes_dict"),
    [
        (A(a=2.0), A(), {"a": 2.0}),
        (A(), A(a=2.0), {"a": 0.0}),
        (B(b="test"), B(), {"b": "test"}),
        (B(), B(b="test1"), {"b": "bar"}),
    ],
)
def test_replace_plain_dataclass(dest_config: object, src_config: object, changes_dict: dict):
    config_replaced = replace(src_config, changes_dict)
    assert config_replaced == dest_config


@pytest.mark.parametrize(
    ("dest_config", "src_config", "changes_dict"),
    [
        (Level1(name="level1_the_potato"), Level1(), {"name": "level1_the_potato"}),
        (Level2(name="level2_bar"), Level2(), {"name": "level2_bar"}),
        (
            Level2(name="level2_bar", prev=Level1(name="level1_good")),
            Level2(),
            {"name": "level2_bar", "prev": {"name": "level1_good"}},
        ),
        (
            Level2(name="level2_bar", prev=Level1(name="level1_good")),
            Level2(),
            {"name": "level2_bar", "prev.name": "level1_good"},
        ),
        (
            Level3(
                name="level3_greatest",
                prev=Level2(name="level2_greater", prev=Level1(name="level1_greate")),
            ),
            Level3(),
            {
                "name": "level3_greatest",
                "prev": {"name": "level2_greater", "prev": {"name": "level1_greate"}},
            },
        ),
        (
            Level3(
                name="level3_greatest",
                prev=Level2(name="level2_greater", prev=Level1(name="level1_greate")),
            ),
            Level3(),
            {
                "name": "level3_greatest",
                "prev.name": "level2_greater",
                "prev.prev.name": "level1_greate",
            },
        ),
    ],
)
def test_replace_nested_dataclasses(dest_config: object, src_config: object, changes_dict: dict):
    config_replaced = replace(src_config, changes_dict)
    assert config_replaced == dest_config


# @pytest.mark.parametrize(
#     ("dest_config", "src_config", "changes_dict"),
#     [
#         (AB(a_or_b=A(a=1.0)), AB(), {"a_or_b": {"a": 1.0}}),
#         (AB(a_or_b=B(b="foo")), AB(a_or_b=B()), {"a_or_b": {"b": "foo"}}),
#         (AB(a_or_b=B(b="bob")), AB(), {"a_or_b": B(b="bob")}),
#         (
#             NestedSubgroupsConfig(ab_or_cd=AB(integer_in_string="2", a_or_b=B(b="bob"))),
#             NestedSubgroupsConfig(ab_or_cd=AB(a_or_b=B())),
#             {"ab_or_cd": {"integer_in_string": "2", "a_or_b": {"b": "bob"}}},
#         ),
#         (
#             NestedSubgroupsConfig(ab_or_cd=AB(integer_in_string="2", a_or_b=B(b="bob"))),
#             NestedSubgroupsConfig(ab_or_cd=AB(a_or_b=B())),
#             {"ab_or_cd.integer_in_string": "2", "ab_or_cd.a_or_b.b": "bob"},
#         ),
#     ],
# )
# def test_replace_nested_subgroups(dest_config: object, src_config: object, changes_dict: dict):
#     config_replaced = replace(src_config, changes_dict)
#     assert config_replaced == dest_config


@pytest.mark.parametrize(
    ("dest_config", "src_config", "changes_dict"),
    [
        (InnerPostInit(in_arg=2.0), InnerPostInit(), {"in_arg": 2.0}),
        (
            OuterPostInit(out_arg=2, inner=(InnerPostInit(3.0, for_outer_post="bar"))),
            OuterPostInit(),
            {"out_arg": 2, "inner": {"in_arg": 3.0, "for_outer_post": "bar"}},
        ),
        (
            OuterPostInit(out_arg=2, inner=(InnerPostInit(3.0, for_outer_post="bar"))),
            OuterPostInit(),
            {"out_arg": 2, "inner.in_arg": 3.0, "inner.for_outer_post": "bar"},
        ),
    ],
)
def test_replace_post_init(dest_config: object, src_config: object, changes_dict: dict):
    config_replaced = replace(src_config, changes_dict)
    assert config_replaced == dest_config


@pytest.mark.parametrize(
    ("dest_config", "src_config", "changes_dict"),
    [
        (
            NestedSubgroupsConfig(ab_or_cd=AB(integer_in_string="2", a_or_b=B(b="bob"))),
            NestedSubgroupsConfig(),
            {"ab_or_cd.integer_in_string": "2", "ab_or_cd.a_or_b.b": "bob"},
        ),
    ],
)
def test_replace_failure_cases(dest_config: object, src_config: object, changes_dict: dict):
    with pytest.raises(Exception):
        config_replaced = replace(src_config, changes_dict)
        assert config_replaced != dest_config


def test_replace_new_values_mixed():
    dest_config = Level3(name="PhD", prev=Level2(name="Master", prev=Level1(name="Undergrad")))
    src_config = Level3()

    replaced_config1 = replace(
        src_config, {"prev": {"name": "Master", "prev": {"name": "Undergrad"}}}, name="PhD"
    )
    assert replaced_config1 == dest_config

    replaced_config2 = replace(
        src_config, name="PhD", prev={"name": "Master", "prev": {"name": "Undergrad"}}
    )
    assert replaced_config2 == dest_config

    replaced_config3 = replace(
        src_config, name="PhD", prev={"name": "Master", "prev.name": "Undergrad"}
    )
    assert replaced_config3 == dest_config
