import os
from dataclasses import dataclass

from simple_parsing.helpers import Serializable


@dataclass
class Person(Serializable):
    name: str = "Bob"
    age: int = 20


@dataclass
class Student(Person):
    domain: str = "Computer Science"
    average_grade: float = 0.80


expected: str = ""

# Serialization:
# We can dump to yaml or json:
charlie = Person(name="Charlie")
print(charlie.dumps_yaml())
expected += """\
age: 20
name: Charlie

"""
print(charlie.dumps_json())
expected += """\
{"name": "Charlie", "age": 20}
"""
print(charlie.dumps())  # JSON by default
expected += """\
{"name": "Charlie", "age": 20}
"""
# Deserialization:
bob = Student()
print(bob)
expected += """\
Student(name='Bob', age=20, domain='Computer Science', average_grade=0.8)
"""

bob.save("bob.yaml")
# Can load a Student from the base class: this will use the first subclass
# that has all the required fields.
_bob = Person.load("bob.yaml", drop_extra_fields=False)
assert isinstance(_bob, Student), _bob
assert _bob == bob

# Cleaning up

os.remove("bob.yaml")
