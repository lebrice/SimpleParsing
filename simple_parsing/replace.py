from __future__ import annotations

import dataclasses
from typing import Any, overload

from simple_parsing.utils import DataclassT, is_dataclass_instance, unflatten_split


@overload
def replace(obj: DataclassT, changes_dict: dict[str, Any]) -> DataclassT:
    ...


@overload
def replace(obj: DataclassT, **changes) -> DataclassT:
    ...


def replace(obj: DataclassT, changes_dict: dict[str, Any] | None = None, **changes) -> DataclassT:
    """Replace some values in a dataclass.

    Compared to `dataclasses.replace`, this has two major differences:
    1. Allows recursively replacing values in nested dataclass fields. When a dictionary is passed
    as the value, and the value of that field on `obj` is a dataclass, then `replace` is called
    recursively.

    2. Allows passing a dictionary of flattened changes, e.g. `{"a.b": 1}` instead of
    `{"a": {"b": 1}}`.

    ## Examples

    >>> import dataclasses
    >>> import simple_parsing
    >>> from typing import Union
    >>> @dataclasses.dataclass
    ... class A:
    ...    a: int = 0
    >>> @dataclasses.dataclass
    ... class B:
    ...     b: str = "b"
    >>> @dataclasses.dataclass
    ... class Config:
    ...     a_or_b: Union[A, B] = dataclasses.field(default_factory=A)

    >>> base_config = Config(a_or_b=A(a=1))


    NOTE: key difference with respect to `dataclasses.replace`:
    >>> dataclasses.replace(base_config, a_or_b={"a": 123})
    Config(a_or_b={'a': 123})
    >>> simple_parsing.replace(base_config, a_or_b={"a": 123})
    Config(a_or_b=A(a=123))

    Replace accepts either a dictionary of changes or keyword arguments:

    >>> simple_parsing.replace(base_config, {"a_or_b": B(b="bob")})
    Config(a_or_b=B(b='bob'))
    >>> simple_parsing.replace(base_config, a_or_b=B(b='bob'))
    Config(a_or_b=B(b='bob'))

    Changes can also be passed in a 'flat' format, which makes it easy to replace nested fields:
    >>> simple_parsing.replace(base_config, {"a_or_b.a": 2})
    Config(a_or_b=A(a=2))
    """
    if changes_dict and changes:
        raise ValueError("Cannot pass both `changes_dict` and `changes`")
    changes = changes_dict or changes
    # changes can be given in a 'flat' format in `changes_dict`, e.g. {"a.b.c": 123}.
    # Unflatten them back to a nested dict (e.g. {"a": {"b": {"c": 123}}})
    changes = unflatten_split(changes)

    replace_kwargs = {}
    for field in dataclasses.fields(obj):
        if field.name not in changes:
            continue
        if not field.init:
            raise ValueError(f"Cannot replace value of non-init field {field.name}.")

        field_value = getattr(obj, field.name)

        if is_dataclass_instance(field_value) and isinstance(changes[field.name], dict):
            field_changes = changes.pop(field.name)
            new_value = replace(field_value, **field_changes)
        else:
            new_value = changes.pop(field.name)
        replace_kwargs[field.name] = new_value

    # note: there may be some leftover values in `changes` that are not fields of this dataclass.
    # we still pass those.
    replace_kwargs.update(changes)

    return dataclasses.replace(obj, **replace_kwargs)
