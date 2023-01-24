from __future__ import annotations

import functools
from dataclasses import dataclass, field

import pytest

from simple_parsing import Serializable, subgroups
from simple_parsing.helpers.serialization import from_dict, to_dict

from ..test_utils import TestSetup


@dataclass
class A(TestSetup):
    a: float = 0.0


@dataclass
class B(TestSetup):
    b: str = "bar"
    b_post_init: str = field(init=False)

    def __post_init__(self):
        self.b_post_init = self.b + "_post"


@dataclass
class AB(TestSetup, Serializable):
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
class NestedSubgroups:
    ab_or_cd: AB | CD = subgroups(
        {"ab": AB, "cd": CD},
        default_factory=AB,
    )


@pytest.mark.parametrize(
    ("config"),
    [
        (A()),
        (AB(a_or_b=A())),
        (NestedSubgroups()),
    ],
)
def test_backward_compatibility_success_cases(config: object):
    new_config = from_dict(
        config.__class__,
        to_dict(config, add_selected_subgroups=False),
        drop_extra_fields=True,
        parse_selection=False,
    )
    assert config == new_config


@pytest.mark.parametrize(
    ("config"),
    [
        (AB(a_or_b=B(b="foo"), integer_in_string="2")),
        (NestedSubgroups(ab_or_cd=CD())),
        (NestedSubgroups(ab_or_cd=CD(c_or_d=D()))),
    ],
)
def test_backward_compatibility_failure_cases(config: object):
    new_config = from_dict(
        config.__class__,
        to_dict(config, add_selected_subgroups=False),
        drop_extra_fields=True,
        parse_selection=False,
    )
    assert config != new_config


@pytest.mark.parametrize(
    ("config"),
    [
        (A()),
        (AB(a_or_b=A())),
        (AB(a_or_b=B(b="foo"), integer_in_string="2")),
        (NestedSubgroups()),
        (NestedSubgroups(ab_or_cd=CD())),
        (NestedSubgroups(ab_or_cd=CD(c_or_d=D()))),
    ],
)
def test_with_selection_info(config: object):
    new_config = from_dict(
        config.__class__,
        to_dict(config, add_selected_subgroups=True),
        drop_extra_fields=True,
        parse_selection=True,
    )
    assert config == new_config
