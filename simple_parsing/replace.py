from __future__ import annotations

from __future__ import annotations
import dataclasses

from typing import Any, overload
from simple_parsing.utils import (
    unflatten_split,
    is_dataclass_instance,
    DataclassT,
)


@overload
def replace(obj: DataclassT, changes_dict: dict[str, Any]) -> DataclassT:
    ...


@overload
def replace(obj: DataclassT, **changes) -> DataclassT:
    ...


def replace(obj: DataclassT, changes_dict: dict[str, Any] | None = None, **changes) -> DataclassT:
    """Replace some values in a dataclass. Also works with nested fields of the dataclass.
    This is essentially an extension of `dataclasses.replace` that also allows changing the nested
    fields of dataclasses.

    ## Examples
    >>> from dataclasses import dataclass, field
    >>> from typing import Union
    >>> @dataclass
    ... class A:
    ...    a: int = 0
    >>> @dataclass
    ... class B:
    ...     b: str = "b"
    >>> @dataclass
    ... class Config:
    ...     a_or_b: Union[A, B] = field(default_factory=A)

    >>> config = Config(a_or_b=A(a=1))

    Replace accepts either a dictionary of changes or keyword arguments:
    >>> replace(config, {"a_or_b": B(b="bob")})
    Config(a_or_b=B(b='bob'))
    >>> replace(config, a_or_b=B(b='bob'))
    Config(a_or_b=B(b='bob'))

    Changes can also be passed in a 'flat' format, which makes it easy to replace nested fields:
    >>> replace(config, {"a_or_b.a": 2})
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
            field_changes = changes[field.name]
            new_value = replace(field_value, **field_changes)
        else:
            new_value = changes[field.name]
        replace_kwargs[field.name] = new_value
    return dataclasses.replace(obj, **replace_kwargs)
