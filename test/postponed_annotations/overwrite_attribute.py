from __future__ import annotations

from dataclasses import dataclass

from ..test_utils import TestSetup
from .overwrite_base import Base, ParamCls


@dataclass
class ParamClsSubclass(ParamCls):
    v: bool


@dataclass
class Subclass(Base, TestSetup):
    attribute: ParamClsSubclass
