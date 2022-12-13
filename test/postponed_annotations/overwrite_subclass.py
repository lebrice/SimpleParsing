from __future__ import annotations

from dataclasses import dataclass

from ..test_utils import TestSetup
from .overwrite_base import Base


@dataclass
class Foo:
    something_else: bool = True


@dataclass
class Subclass(Base, TestSetup):
    other_attribute: Foo
