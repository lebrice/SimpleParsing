import math
from dataclasses import dataclass, fields


@dataclass
class Point:
    """Simple class Point."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def distance(self, other: "Point") -> float:
        return math.sqrt(
            (self.x - other.x) ** 2 + (self.y - other.y) ** 2 + (self.z - other.z) ** 2
        )


p1 = Point(x=1, y=3)
p2 = Point(x=1.0, y=3.0)

assert p1 == p2

for field in fields(p1):
    print(f"Field {field.name} has type {field.type} and a default value if {field.default}.")

expected = """
Field x has type <class 'float'> and a default value if 0.0.
Field y has type <class 'float'> and a default value if 0.0.
Field z has type <class 'float'> and a default value if 0.0.
"""
