from dataclasses import dataclass

from ..test_utils import TestSetup
from .a import A


@dataclass
class B(A, TestSetup):
    v: int
