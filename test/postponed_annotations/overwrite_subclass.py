from __future__ import annotations
from .overwrite_base import Base
from dataclasses import dataclass
from ..test_utils import TestSetup

@dataclass
class Foo:
    something_else: bool = True

@dataclass
class Subclass(Base, TestSetup):
    other_attribute: Foo