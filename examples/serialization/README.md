# Serialization

The `Serializable` class makes it easy to serialize any dataclass to and from json or yaml.
It is also very easy to add support for serializing/deserializing your own custom types!

```python
>>> from simple_parsing.helpers import Serializable
>>> from dataclasses import dataclass
>>>
>>> @dataclass
... class Person(Serializable):
...     name: str = "Bob"
...     age: int = 20
...
>>> @dataclass
... class Student(Person):
...     domain: str = "Computer Science"
...     average_grade: float = 0.80
...
>>> # Serialization:
... # We can dump to yaml or json:
... charlie = Person(name="Charlie")
>>> print(charlie.dumps_yaml())
age: 20
name: Charlie

>>> print(charlie.dumps_json())
{"name": "Charlie", "age": 20}
>>> print(charlie.dumps()) # JSON by default
{"name": "Charlie", "age": 20}
>>> # Deserialization:
... bob = Student()
>>> print(bob)
Student(name='Bob', age=20, domain='Computer Science', average_grade=0.8)
>>> bob.save("bob.yaml")
>>> # Can load a Student from the base class: this will use the first subclass
... # that has all the required fields.
... _bob = Person.load("bob.yaml", drop_extra_fields=False)
>>> assert isinstance(_bob, Student)
>>> assert _bob == bob
```

## Adding custom types

Register a new encoding function using `encode`, and a new decoding function using `register_decoding_fn`

For example: Consider the same example as above, but we add a Tensor attribute from `pytorch`.

```python
from dataclasses import dataclass
from typing import List

import torch
from torch import Tensor

from simple_parsing.helpers import Serializable
from simple_parsing.helpers.serialization import encode, register_decoding_fn

expected: str = ""

@dataclass
class Person(Serializable):
    name: str = "Bob"
    age: int = 20
    t: Tensor = torch.arange(4)


@dataclass
class Student(Person):
    domain: str = "Computer Science"
    average_grade: float = 0.80


@encode.register
def encode_tensor(obj: Tensor) -> List:
    """ We choose to encode a tensor as a list, for instance """
    return obj.tolist()

# We will use `torch.as_tensor` as our decoding function
register_decoding_fn(Tensor, torch.as_tensor)

# Serialization:
# We can dump to yaml or json:
charlie = Person(name="Charlie")
print(charlie.dumps_yaml())
expected += """\
age: 20
name: Charlie
t:
- 0
- 1
- 2
- 3

"""


print(charlie.dumps_json())
expected += """\
{"name": "Charlie", "age": 20, "t": [0, 1, 2, 3]}
"""

# Deserialization:
bob = Student()
print(bob)
expected += """\
Student(name='Bob', age=20, t=tensor([0, 1, 2, 3]), domain='Computer Science', average_grade=0.8)
"""

# Can load a Student from the base class: this will use the first subclass
# that has all the required fields.
bob.save("bob.yaml")
_bob = Person.load("bob.yaml", drop_extra_fields=False)
assert isinstance(_bob, Student), _bob
# Note: using _bob == bob doesn't work here because of Tensor comparison,
# But this basically shows the same thing as the previous example.
assert str(_bob) == str(bob)

```
