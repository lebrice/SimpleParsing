from dataclasses import dataclass
from .a import A
from ..test_utils import TestSetup

@dataclass
class B(A, TestSetup):
    v: int
