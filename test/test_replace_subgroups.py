from __future__ import annotations

import functools
import logging
from dataclasses import dataclass, field
from typing import Union

import pytest

from simple_parsing import replace_subgroups, subgroups

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
    a_or_b: A | B = subgroups({"A": A, "B": B},default_factory=A)
    
    
def test_replace_subgroups():
    src_config = AB()
    dest_config = AB(a_or_b=B(b='bob'))
    
    assert replace_subgroups(src_config, {'a_or_b.b': "bob"}, subgroup_changes={'a_or_b': 'B'}) == dest_config
    