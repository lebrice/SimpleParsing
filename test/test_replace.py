from __future__ import annotations

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
class InnerPostInit:
    in_arg: float = 1.0
    in_arg_post: str= field(init=False)
    for_outer_post: str = 'foo'
    
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
        self.arg_post_on_inner = self.inner.for_outer_post + '_outer'

@pytest.mark.parametrize(
    ("dest_config", "src_config", "changes_dict"),
    [
        (A(a=2.0), A(), {"a": 2.0}),
        (B(b="test"), B(), {"b": "test"}),
    ]
)
def test_replace_plain_dataclass(dest_config: object, src_config: object, changes_dict: dict):
    config_replaced = replace(src_config, changes_dict)
    assert config_replaced == dest_config
    

def test_replace_nested_dataclasses():
    ...
    
def test_replace_subgroups():
    ...
    
def test_replace_nested_subgroups():
    ...
    

@pytest.mark.parametrize(
    ("dest_config", "src_config", "changes_dict"),
    [
        (
            InnerPostInit(in_arg=2.0), InnerPostInit(), {"in_arg": 2.0}
        ),
        (
            OuterPostInit(out_arg=2, inner=(InnerPostInit(3.0, for_outer_post='bar'))),
            OuterPostInit(),
            {"out_arg": 2, "inner": {"in_arg": 3.0, "for_outer_post": "bar"}}
        ),
    ]
)
def test_replace_post_init(dest_config: object, src_config: object, changes_dict: dict):
    config_replaced = replace(src_config, changes_dict)
    assert config_replaced == dest_config
    
def test_replace_new_values_mixed():
    ...

def test_replace_raises():
    ...