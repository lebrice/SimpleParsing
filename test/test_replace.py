from __future__ import annotations

import functools
import logging
from dataclasses import dataclass, field

import pytest

from simple_parsing import replace
from simple_parsing.utils import Dataclass, DataclassT

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
class UnionConfig:
    a_or_b: A | B = field(default_factory=A)


@dataclass
class WithOptional:
    optional_a: A | None = None


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
    ("start", "changes", "expected"),
    [
        (A(), {"a": 2.0}, A(a=2.0)),
        (A(a=2.0), {"a": 0.0}, A()),
        (B(), {"b": "test"}, B(b="test")),
        (B(b="test1"), {"b": "bar"}, B(b="bar")),
        (
            UnionConfig(a_or_b=A(a=1.0)),
            {"a_or_b": B(b="bob")},
            UnionConfig(a_or_b=B(b="bob")),
        ),
        (
            UnionConfig(a_or_b=A(a=1.0)),
            {"a_or_b.a": 2.0},
            UnionConfig(a_or_b=A(a=2.0)),
        ),
        # NOTE: This looks like we're converting a dict to a dataclass, but we're just replacing
        # the only field on the `A` object.
        (
            WithOptional(optional_a=A(a=0)),
            {"optional_a": {"a": 123}},
            WithOptional(optional_a=A(a=123)),
        ),
        # Test dataclasses with a non-init field and a __post_init__ method:
        (
            InnerPostInit(),
            {"in_arg": 2.0},
            InnerPostInit(in_arg=2.0),
        ),
        (
            OuterPostInit(),
            {"out_arg": 2, "inner": {"in_arg": 3.0, "for_outer_post": "bar"}},
            OuterPostInit(out_arg=2, inner=(InnerPostInit(3.0, for_outer_post="bar"))),
        ),
        (
            OuterPostInit(),
            {"out_arg": 2, "inner.in_arg": 3.0, "inner.for_outer_post": "bar"},
            OuterPostInit(out_arg=2, inner=(InnerPostInit(3.0, for_outer_post="bar"))),
        ),
    ],
)
def test_replace(start: DataclassT, changes: dict, expected: DataclassT):
    actual = replace(start, **changes)
    assert actual == expected


@pytest.mark.parametrize(
    ("start", "changes", "expected"),
    [
        (
            Level1(),
            {"name": "level1_the_potato"},
            Level1(name="level1_the_potato"),
        ),
        (
            Level2(),
            {"name": "level2_bar"},
            Level2(name="level2_bar"),
        ),
        (
            Level2(),
            {"name": "level2_bar", "prev": {"name": "level1_good"}},
            Level2(name="level2_bar", prev=Level1(name="level1_good")),
        ),
        (
            Level2(),
            {"name": "level2_bar", "prev.name": "level1_good"},
            Level2(name="level2_bar", prev=Level1(name="level1_good")),
        ),
        (
            Level3(),
            {
                "name": "level3_greatest",
                "prev": {"name": "level2_greater", "prev": {"name": "level1_greate"}},
            },
            Level3(
                name="level3_greatest",
                prev=Level2(name="level2_greater", prev=Level1(name="level1_greate")),
            ),
        ),
        (
            Level3(),
            {
                "name": "level3_greatest",
                "prev.name": "level2_greater",
                "prev.prev.name": "level1_great",
            },
            Level3(
                name="level3_greatest",
                prev=Level2(name="level2_greater", prev=Level1(name="level1_great")),
            ),
        ),
    ],
)
@pytest.mark.parametrize("pass_dict_as_kwargs", [True, False])
def test_replace_nested_dataclasses(
    start: DataclassT, changes: dict, expected: DataclassT, pass_dict_as_kwargs: bool
):
    actual = replace(start, **changes) if pass_dict_as_kwargs else replace(start, changes)
    assert actual == expected


@pytest.mark.parametrize(
    ("start", "changes", "exception_type", "match"),
    [
        (
            UnionConfig(a_or_b=A(a=1.0)),
            {"a_or_b.b": "bob"},
            TypeError,
            "unexpected keyword argument 'b'",
        ),
        (
            A(a=123),
            {"not_a_field": 456},
            TypeError,
            "unexpected keyword argument 'not_a_field'",
        ),
        (
            A(a=123),
            {"a_bad_field": {"foo": "bar"}},
            TypeError,
            "unexpected keyword argument 'a_bad_field'",
        ),
        (
            WithOptional(optional_a=None),
            {"foo.bar": {"a": 123}},
            TypeError,
            "unexpected keyword argument 'foo'",
        ),
        pytest.param(
            WithOptional(optional_a=None),
            {"optional_a.a": 123},
            # NOTE: This probably to be fixed... looks counter-intuitive. it's an artifact of us
            # converting {"optional_a.a": 123} to {"optional_a": {"a": 123}}. However, there's no
            # easy way to fix these cases without inspecting the type annotations of the fields,
            # which adds a lot of complexity.
            TypeError,
            "<todo>",
            marks=pytest.mark.xfail(strict=True, reason="TODO: Potentially ambiguous."),
        ),
    ],
)
@pytest.mark.parametrize("pass_dict_as_kwargs", [True, False])
def test_replace_invalid(
    start: Dataclass,
    changes: dict,
    exception_type: type[Exception],
    match: str,
    pass_dict_as_kwargs: bool,
):
    with pytest.raises(exception_type, match=match):
        if pass_dict_as_kwargs:
            replace(start, **changes)
        else:
            replace(start, changes)
