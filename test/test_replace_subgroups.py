from __future__ import annotations

from dataclasses import dataclass, field

from simple_parsing import replace_subgroups, subgroups


@dataclass
class A:
    a: float = 0.0


@dataclass
class B:
    b: str = "bar"


@dataclass
class AorB:
    a_or_b: A | B = subgroups({"a": A, "b": B}, default_factory=A)


@dataclass(frozen=True)
class FrozenConfig:
    a: int = 1
    b: str = "bob"


odd = FrozenConfig(a=1, b="odd")
even = FrozenConfig(a=2, b="even")


@dataclass
class Config:
    subgroup: A | B = subgroups({"a": A, "b": B}, default_factory=A)
    frozen_subgroup: FrozenConfig = subgroups({"odd": odd, "even": even}, default=odd)
    optional: A | None = None
    implicit_optional: A = None
    union: A | B = field(default_factory=A)
    nested_subgroup: AorB = field(default_factory=AorB)


def test_replace_subgroups():
    c = Config()
    assert replace_subgroups(c, {"subgroup": "b"}) == Config(subgroup=B())
    assert replace_subgroups(c, {"frozen_subgroup": "odd"}) == Config(frozen_subgroup=odd)
    assert replace_subgroups(c, {"optional": A}) == Config(optional=A())
    assert replace_subgroups(c, {"implicit_optional": A}) == Config(implicit_optional=A())
    assert replace_subgroups(c, {"union": B}) == Config(union=B())
    assert replace_subgroups(c, {"nested_subgroup.a_or_b": "b"}) == Config(
        nested_subgroup=AorB(a_or_b=B())
    )
    assert replace_subgroups(c, {"nested_subgroup": {"a_or_b": "b"}}) == Config(
        nested_subgroup=AorB(a_or_b=B())
    )
