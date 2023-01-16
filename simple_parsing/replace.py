from __future__ import annotations

from dataclasses import fields
from typing import Iterable

from simple_parsing.helpers.serialization.serializable import from_dict, to_dict

from .utils import (
    Dataclass,
    DataclassT,
    dict_union,
    is_dataclass_instance,
    unflatten_split,
)


def replace(
    dataclass: DataclassT, new_values_dict: dict | None = None, **new_values: dict
) -> DataclassT:
    """Replace some values in a dataclass. Also works with nested fields of the dataclass.

    This is essentially an extension of `dataclasses.replace` that also allows changing the nested
    fields of dataclasses.

    ## Examples

    ```python
    from dataclasses import dataclass, field
    from typing import Union
    @dataclass
    class A:
        a: int = 0

    @dataclass
    class B:
       b: str = "b"

    @dataclass
    class Config:
       a_or_b: A | B = field(default_factory=A)

    config = Config(a_or_b=A(a=1))
    assert replace(config, {"a_or_b": {"a": 2}}) == Config(a_or_b=A(a=2))
    assert replace(config, {"a_or_b.a": 2}) == Config(a_or_b=A(a=2))
    assert replace(config, {"a_or_b": B(b="bob")}) == Config(a_or_b=B(b='bob'))
    ```
    """

    if new_values_dict:
        new_values = dict(**new_values_dict, **new_values)

    # TODO: Also encode the class to use for the subgroup fields here somehow.
    dataclass_dict = to_dict(dataclass, recurse=True)
    nested_field_types = dict(_nested_field_types(dataclass))
    # Note: we also accept the nested fields in a flattened format (e.g. {"a.b.c.d": 123})
    new_values = unflatten_split(new_values)

    new_dataclass_dict = dict_union(dataclass_dict, new_values, recurse=True)
    return _from_dict_with_nested_field_types(
        type(dataclass), new_dataclass_dict, nested_field_types
    )


def _from_dict_with_nested_field_types(
    dataclass_type: type[DataclassT],
    dataclass_dict: dict,
    nested_field_types: dict[str, type[Dataclass]],
    _prefix: str = "",
) -> DataclassT:
    """A version of `from_dict` that uses the prescribed types for nested dataclass fields."""
    dataclass_kwargs = {}
    for key, value in dataclass_dict.items():
        field_prefix = (_prefix + "." if _prefix else "") + key
        if is_dataclass_instance(value):
            dataclass_kwargs[key] = value
        elif field_prefix in nested_field_types:
            dataclass_type_to_use = nested_field_types[field_prefix]
            dataclass_kwargs[key] = _from_dict_with_nested_field_types(
                dataclass_type_to_use, value, nested_field_types, _prefix=field_prefix
            )
        else:
            dataclass_kwargs[key] = value
    # note: We can now just call `from_dict` and pass a dataclass instance for a nested field, and
    # it will just use that value.

    return from_dict(dataclass_type, dataclass_kwargs, drop_extra_fields=True)


def _nested_field_types(dataclass: Dataclass) -> Iterable[tuple[str, type[Dataclass]]]:
    """Returns an iterator that yields the paths to dataclass fields and their types in a given
    dataclass tree.
    """
    path = ""
    for field in fields(dataclass):
        value = getattr(dataclass, field.name)
        if not is_dataclass_instance(value):
            continue

        prefix = path + "." if path else ""
        yield prefix + field.name, type(value)

        for nested_field_path, field_type in _nested_field_types(value):
            yield prefix + field.name + "." + nested_field_path, field_type
