from __future__ import annotations

import functools
from dataclasses import dataclass, field, replace

import pytest

from simple_parsing.helpers.serialization import from_dict, to_dict
from simple_parsing.utils import Dataclass


def test_replace_and_from_dict_already_call_post_init():
    n_post_init_calls = 0

    @dataclass
    class Bob:
        a: int = 123

        def __post_init__(self):
            nonlocal n_post_init_calls
            n_post_init_calls += 1

    assert n_post_init_calls == 0
    bob = Bob()
    assert n_post_init_calls == 1
    _ = replace(bob, a=456)
    assert n_post_init_calls == 2

    _ = from_dict(Bob, {"a": 456})
    assert n_post_init_calls == 3


@dataclass
class InnerConfig:
    arg1: int = 1
    arg2: str = "foo"
    arg1_post_init: str = field(init=False)

    def __post_init__(self):
        self.arg1_post_init = str(self.arg1)


@dataclass
class OuterConfig1:
    out_arg: int = 0
    inner: InnerConfig = field(default_factory=InnerConfig)


@dataclass
class OuterConfig2:
    out_arg: int = 0
    inner: InnerConfig = field(default_factory=functools.partial(InnerConfig, arg2="bar"))


@dataclass
class Level1:
    arg: int = 1


@dataclass
class Level2:
    arg: int = 1
    prev: Level1 = field(default_factory=Level1)


@dataclass
class Level3:
    arg: int = 1
    prev: Level2 = field(default_factory=Level2)


@pytest.mark.parametrize(
    ("config"),
    [
        OuterConfig1(),
        OuterConfig2(),
        Level1(arg=2),
        Level2(arg=2, prev=Level1(arg=3)),
        Level2(),
        Level3(),
    ],
)
def test_issue_210_nested_dataclasses_serialization(config: Dataclass):
    _from_dict = functools.partial(from_dict, type(config))
    assert _from_dict(to_dict(config)) == config
    assert _from_dict(to_dict(config), drop_extra_fields=True) == config
    # More 'intense' comparisons, to make sure that the serialization is reversible:
    assert to_dict(_from_dict(to_dict(config))) == to_dict(config)
    assert _from_dict(to_dict(_from_dict(to_dict(config)))) == _from_dict(to_dict(config))
