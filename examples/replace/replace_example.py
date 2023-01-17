from __future__ import annotations

from dataclasses import dataclass, field

import simple_parsing as sp
from simple_parsing import subgroups


@dataclass
class InnerClass:
    arg1: int = 0
    arg2: str = "foo"


@dataclass(frozen=True)
class OuterClass:
    outarg: int = 1
    nested: InnerClass = InnerClass()


changes_1 = {"outarg": 2, "nested.arg1": 1, "nested.arg2": "bar"}
changes_2 = {"outarg": 2, "nested": {"arg1": 1, "arg2": "bar"}}
c = OuterClass()
c1 = sp.replace(c, changes_1)
c2 = sp.replace(c, changes_2)
assert c1 == c2


@dataclass
class A:
    a: float = 0.0


@dataclass
class B:
    b: str = "bar"


@dataclass
class NestedConfig:
    str_arg: str = "default"
    int_arg: int = 0


@dataclass
class AB:
    integer_only_by_post_init: int = field(init=False)
    integer_in_string: str = "1"
    nested: NestedConfig = field(default_factory=NestedConfig)
    a_or_b: A | B = subgroups({"a": A, "b": B}, default="a")

    def __post_init__(self):
        self.integer_only_by_post_init = int(self.integer_in_string)


config = AB()
new_config = sp.replace(
    config,
    {
        "__subgroups__@a_or_b": "b",
        "a_or_b.b": "test",
        "integer_in_string": "2",
        "nested": {
            "str_arg": "in_nested",
            "int_arg": 100,
        },
    },
)


assert new_config.a_or_b.b == "test"
assert new_config.integer_in_string == "2"
assert new_config.integer_only_by_post_init == 2
assert new_config.nested.str_arg == "in_nested"
assert new_config.nested.int_arg == 100
assert id(config) != id(new_config)
