from __future__ import annotations
import dataclasses
from simple_parsing.utils import is_dataclass_instance, DataclassT, unflatten_split
from typing import Any, overload
from simple_parsing.helpers.subgroups import Key


@overload
def replace_subgroups(obj: DataclassT, changes_dict: dict[str, Any],  subgroup_changes: dict[str, Key] | None = None) -> DataclassT:
    ...
    
    
@overload
def replace_subgroups(obj: DataclassT,  subgroup_changes: dict[str, Key] | None = None, **changes) -> DataclassT:
    ...
    
    
def replace_subgroups(obj: DataclassT, changes_dict: dict[str, Any] | None = None, subgroup_changes: dict[str, Key] | None = None, **changes) -> DataclassT:
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
            raise ValueError(
                f"Cannot replace value of non-init field {field.name}.")

        field_value = getattr(obj, field.name)

        if is_dataclass_instance(field_value):
            if field.metadata.get('subgroups', None) and subgroup_changes is not None:
                field_value = field.metadata['subgroups'][subgroup_changes[field.name]]()
                field_changes = changes[field.name]
                new_value = replace_subgroups(field_value, field_changes, subgroup_changes)
            elif isinstance(changes[field.name], dict):
                field_changes = changes[field.name]
                new_value = replace_subgroups(field_value, field_changes, subgroup_changes)
        else:
            new_value = changes[field.name]
        replace_kwargs[field.name] = new_value
    return dataclasses.replace(obj, **replace_kwargs)