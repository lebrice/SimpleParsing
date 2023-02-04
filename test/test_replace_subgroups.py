from __future__ import annotations

import functools
import logging
from dataclasses import dataclass, field

import pytest

from simple_parsing import replace_subgroups, subgroups
from simple_parsing.utils import Dataclass, DataclassT

logger = logging.getLogger(__name__)


@dataclass
class A():
    a: float = 0.0


@dataclass
class B():
    b: str = "bar"
    b_post_init: str = field(init=False)

    def __post_init__(self):
        self.b_post_init = self.b + "_post"


@dataclass
class WithOptional:
    optional_a: A | None = None


@dataclass
class AB():
    integer_only_by_post_init: int = field(init=False)
    integer_in_string: str = "1"
    a_or_b: A | B = subgroups(
        {
            "a": A,
            "a_1.23": functools.partial(A, a=1.23),
            "b": B,
            "b_bob": functools.partial(B, b="bob"),
        },
        default="a",
    )

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


@pytest.mark.parametrize(
    ("start", "changes", "subgroup_changes", "expected"),
    [
        (
            AB(),
            {"a_or_b": {"a": 1.0}},
            None,
            AB(a_or_b=A(a=1.0)), 
        ),
        (
            AB(a_or_b=B()),
            {"a_or_b": {"b": "foo"}}, 
            None, 
            AB(a_or_b=B(b="foo"))
        ), 
        (
            AB(),
            {"a_or_b": {"b": "foo"}}, 
            {"a_or_b": "b"}, 
            AB(a_or_b=B(b="foo"))
        ), 
        (
            AB(),
            {"a_or_b": B(b="bob")},
            None,
            AB(a_or_b=B(b="bob")), 
        ),
        (
            NestedSubgroupsConfig(ab_or_cd=AB(a_or_b=B())),
            {"ab_or_cd": {"integer_in_string": "2", "a_or_b": {"b": "bob"}}},
            None,
            NestedSubgroupsConfig(ab_or_cd=AB(
                integer_in_string="2", a_or_b=B(b="bob"))),
        ),
        (
            NestedSubgroupsConfig(ab_or_cd=AB(a_or_b=B())),
            {"ab_or_cd.integer_in_string": "2", "ab_or_cd.a_or_b.b": "bob"},
            None,
            NestedSubgroupsConfig(ab_or_cd=AB(
                integer_in_string="2", a_or_b=B(b="bob"))),
        ),
        (
            NestedSubgroupsConfig(),
            {"ab_or_cd.integer_in_string": "2", "ab_or_cd.a_or_b.b": "bob"},
            {"ab_or_cd": 'ab', "ab_or_cd.a_or_b": 'b'},
            NestedSubgroupsConfig(ab_or_cd=AB(
                integer_in_string="2", a_or_b=B(b="bob"))),
        ),
        (
            NestedSubgroupsConfig(),
            None,
            {"ab_or_cd": 'cd', "ab_or_cd.c_or_d": 'd'},
            NestedSubgroupsConfig(ab_or_cd=CD(c_or_d=D())),
        ),
        (
            NestedSubgroupsConfig(),
            {"ab_or_cd.c_or_d.d": 1},
            {"ab_or_cd": 'cd', "ab_or_cd.c_or_d": 'd'},
            NestedSubgroupsConfig(ab_or_cd=CD(c_or_d=D(d=1))),
        ),
    ],
)
def test_replace_subgroups(start: DataclassT, changes: dict, subgroup_changes: dict, expected: DataclassT):
    actual = replace_subgroups(
        start, changes, subgroup_changes)
    assert actual == expected
