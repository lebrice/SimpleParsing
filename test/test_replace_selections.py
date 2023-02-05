from __future__ import annotations

import copy
import functools
import logging
from dataclasses import dataclass, field, fields
from enum import Enum
from pathlib import Path
from typing import Tuple

import pytest

from simple_parsing import replace_selections, subgroups
from simple_parsing.helpers.subgroups import Key
from simple_parsing.replace_selections import replace_selected_dataclass
from simple_parsing.utils import DataclassT

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

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3

@dataclass
class AllTypes:
    arg_int : int = 0
    arg_float: float = 1.0
    arg_str: str = 'foo'
    arg_list: list = field(default_factory= lambda: [1,2])
    arg_dict : dict = field(default_factory=lambda : {"a":1 , "b": 2})
    arg_union: str| Path = './'
    arg_tuple: Tuple[int, int] = (1,1)
    arg_enum: Color = Color.BLUE
    arg_dataclass: A = field(default_factory=A)
    arg_subgroups: A | B = subgroups(
        {
            "a": A,
            "a_1.23": functools.partial(A, a=1.23),
            "b": B,
            "b_bob": functools.partial(B, b="bob"),
        },
        default="a",
    )
    arg_optional: A | None = None
    arg_union_dataclass: A | B = field(default_factory=A)
    arg_union_dataclass_init_false: A | B = field(init=False)
    
    def __post_init__(self):
        self.arg_union_dataclass_init_false = copy.copy(self.arg_union_dataclass)
        

@pytest.mark.parametrize(
    ("start", "changes", "selections", "expected"),
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
        (
            AllTypes(),
            {"arg_subgroups.b": "foo","arg_optional.a": 1.0},
            {"arg_subgroups": "b", "arg_optional": A},
            AllTypes(arg_subgroups=B(b="foo"), arg_optional=A(a=1.0))
        ),
    ],
)
def test_replace_selections(start: DataclassT, changes: dict, selections: dict, expected: DataclassT):
    actual = replace_selections(
        start, changes, selections)
    assert actual == expected


@pytest.mark.parametrize(
    ('start', 'changes', 'expected'),
    [
        (
            AllTypes(), 
            {'arg_subgroups':'b',"arg_optional": A},
            AllTypes(arg_subgroups=B(), arg_optional=A())
        ),
        (
            AllTypes(), 
            {'arg_subgroups': B,"arg_optional": A},
            AllTypes(arg_subgroups=B(), arg_optional=A())
        ),
        (
            AllTypes(arg_optional=A()), 
            {'arg_subgroups': B,"arg_optional": None},
            AllTypes(arg_subgroups=B(), arg_optional=None)
        ),
        (
            AllTypes(arg_optional=A(a=1.0)), 
            {"arg_optional": A},
            AllTypes(arg_optional=A())
        ),
        (
            AllTypes(arg_optional=None), 
            {"arg_optional": A(a=1.2)},
            AllTypes(arg_optional=A(a=1.2))
        ),
        (
            AllTypes(arg_subgroups=A(a=1.0)), 
            {'arg_subgroups': 'a'},
            AllTypes(arg_subgroups=A())
        ),
        (
            AllTypes(arg_subgroups=A(a=1.0)), 
            None,
            AllTypes(arg_subgroups=A(a=1.0))
        ),
        (
            AllTypes(arg_subgroups=A(a=1.0)), 
            {},
            AllTypes(arg_subgroups=A(a=1.0))
        ),
        (
            NestedSubgroupsConfig(),
            {"ab_or_cd": 'cd', "ab_or_cd.c_or_d": 'd'},
            NestedSubgroupsConfig(ab_or_cd=CD(c_or_d=D()))
        ),
    ]
)
def test_replace_union_dataclasses(start: DataclassT, changes:dict[str, Key|DataclassT], expected: DataclassT):
    assert replace_selected_dataclass(start, changes) == expected