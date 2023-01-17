# The extended `replace` for simple-parsing

The replace function of the dataclasses module has the signature of [`Dataclasses.replace(obj, /, **changes)`](https://docs.python.org/3/library/dataclasses.html#dataclasses.replace):
- it creates a new object of the same type as `obj`, replacing fields with values from changes.
- If obj is not a Data Class, raises TypeError. If values in changes do not specify fields, raises TypeError.

However, the `Dataclass.replace` doesn't work with nested dataclasses, subgroups, and other features in `simple-parsing`. To solve this, the `simple_parsing.replace` should be supplemented as an extension to `dataclasses.replace`.

# The signature of `simple_parsing.replace`
```def replace(obj: object, changes: Dict[str, Any]):```
- obj: object

    If obj is not a dataclass instance, raises TypeError

- changes: Dict[str, Any]

    The dictionary can be nested or flatten structure which is especially useful for frozen classes.

# A Basic example
```python
from dataclasses import dataclass, field


@dataclass
class InnerClass:
    arg1: int = 0
    arg2: str = "foo"

@dataclass(frozen=True)
class OuterClass:
    outarg: int = 1
    nested: InnerClass = field(default_factory=InnerClass)

changes_1 = {"outarg": 2, "nested.arg1": 1, "nested.arg2": "bar"}
changes_2 = {"outarg": 2, "nested": {"arg1": 1, "arg2": "bar"}}
c = OuterClass()
c1 = replace(c, changes_1)
c2 = replace(c, changes_2)
assert c1 == c2
```

# A more complicated example
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
    str_arg: str = 'default'
    int_arg: int = 0


@dataclass
class AB:
    integer_only_by_post_init: int = field(init=False)
    integer_in_string: str = '1'
    nested: NestedConfig = field(default_factory=NestedConfig)
    a_or_b: A | B = subgroups({"a": A, "b": B}, default='a')

    def __post_init__(self):
        self.integer_only_by_post_init = int(self.integer_in_string)


config = AB()
new_config = sp.replace(
    config,
    {
        'a_or_b': 'b',
        'a_or_b.b': 'test',
        'integer_in_string': '2',
        "nested": {
            "str_arg": "in_nested",
            "int_arg": 100,
        }
    }
)


assert new_config.a_or_b.b == 'test'
assert new_config.integer_in_string == '2'
assert new_config.integer_only_by_post_init == 2
assert new_config.nested.str_arg == 'in_nested'
assert new_config.nested.int_arg == 100
assert id(config) != id(new_config)

```