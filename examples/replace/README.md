# The extended `replace` for simple-parsing

The replace function of the dataclasses module has the signature  of [`Dataclasses.replace(obj, /, **changes)`](https://docs.python.org/3/library/dataclasses.html#dataclasses.replace):
- it creates a new object of the same type as `obj`, replacing fields with values from changes.
- If obj is not a Data Class, raises TypeError. If values in changes do not specify fields, raises TypeError.

However, the `Dataclass.replace` doesn't work with nested dataclasses, subgroups, and other features in `simple-parsing`. To solve this, the `simple_parsing.replace` should be supplemented as an extension to `dataclasses.replace`.

```python
from __future__ import annotations
from dataclasses import dataclass, field
from simple_parsing import subgroups
import simple_parsing as sp

@dataclass
class A:
    a: float = 0.0

@dataclass
class B:
    b: str = "bar"

@dataclass
class NestedConfig:
    nested_str: str = 'in_nested'
    nested_int: int = 0

@dataclass
class AB:
    integer_only_by_post_init: int = field(init=False)
    integer_in_string: str = '1'
    nested: NestedConfig = NestedConfig()
    a_or_b: A | B = subgroups({"a": A, "b": B}, default='a')

    def __post_init__(self):
        self.integer_only_by_post_init = int(self.integer_in_string)
        
config = AB(a_or_b='a')
new_config = sp.replace(
    config, 
    {
        'a_or_b': 'b',
        'a_or_b.b': 'test',
        'integer_in_string': 2,
        'nested.nested_str'
    }
)

assert config == new_config
assert id(config) != id(new_config)
```