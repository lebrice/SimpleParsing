from __future__ import annotations

import functools
from dataclasses import dataclass, field

import pytest

from simple_parsing.helpers.serialization import from_dict, to_dict
from simple_parsing.utils import Dataclass


@dataclass
class Level1:
    arg: int = 1


@dataclass
class Level2:
    arg: int = 1
    prev: Level1 = field(default_factory=Level1)


@pytest.mark.parametrize(
    "config",
    [
        Level1(arg=2),
        Level2(arg=2, prev=Level1(arg=3)),
    ],
)
def test_nested_dataclass(config: Dataclass):
    _from_dict = functools.partial(from_dict, type(config))
    assert _from_dict(to_dict(config)) == config
    assert _from_dict(to_dict(config), drop_extra_fields=True) == config

    assert to_dict(_from_dict(to_dict(config))) == to_dict(config)
    assert _from_dict(to_dict(_from_dict(to_dict(config)))) == _from_dict(to_dict(config))
