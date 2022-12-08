from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Foo:
    ...
    
@dataclass
class Base:
    a: Foo