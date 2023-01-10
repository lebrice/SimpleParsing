from __future__ import annotations

from dataclasses import dataclass

from ..test_utils import TestSetup
from .b import B


@dataclass
class P1(TestSetup):
    a1: int = 1


@dataclass
class P2(P1):
    a2: int = 2


@dataclass
class P3(P2):
    a3: int = 3


@dataclass
class P4(P3):
    a4: int = 4


@dataclass
class C(B):
    m: str
