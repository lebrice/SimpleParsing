from __future__ import annotations
import dataclasses
from simple_parsing.utils import is_dataclass_instance, DataclassT, unflatten_split
from typing import Any, overload
from simple_parsing.helpers.subgroups import Key


def unflatten_subgroup_changes(subgroup_changes: dict[str, Key]):
    dc = {}
    for k, v in subgroup_changes.items():
        if '__key__' != k and '.' not in k:
            dc[k+'.__key__'] = v
        else:
            dc[k] = v
    
    return unflatten_split(dc)


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

    if subgroup_changes:
        subgroup_changes = unflatten_subgroup_changes(subgroup_changes)
        
    replace_kwargs = {}
    for field in dataclasses.fields(obj):
        if field.name in changes:
            if not field.init:
                raise ValueError(f"Cannot replace value of non-init field {field.name}.")

            field_value = getattr(obj, field.name)

            if is_dataclass_instance(field_value) and isinstance(changes[field.name], dict):
                field_changes = changes.pop(field.name)
                sub_subgroup_changes = subgroup_changes
                if subgroup_changes and field.name in subgroup_changes:
                    sub_subgroup_changes = subgroup_changes.pop(field.name)
                    key = sub_subgroup_changes.pop("__key__", None)
                    if key and field.metadata.get('subgroups') and key in field.metadata['subgroups']:
                        field_value = field.metadata['subgroups'][key]()
                new_value = replace_subgroups(field_value, field_changes, sub_subgroup_changes)
            else:
                new_value = changes.pop(field.name)
            replace_kwargs[field.name] = new_value
        elif subgroup_changes and field.name in subgroup_changes:
            if not field.init:
                raise ValueError(f"Cannot replace value of non-init field {field.name}.")
            
            sub_subgroup_changes = subgroup_changes.pop(field.name)
            key = sub_subgroup_changes.pop("__key__", None)
            if key and field.metadata.get('subgroups') and key in field.metadata['subgroups']:
                field_value = field.metadata['subgroups'][key]()
                new_value = replace_subgroups(field_value, None, sub_subgroup_changes)
            else:
                field_value = getattr(obj, field.name)
                new_value = replace_subgroups(field_value, None, sub_subgroup_changes)
            replace_kwargs[field.name] = new_value
        else:
            continue
                
    # note: there may be some leftover values in `changes` that are not fields of this dataclass.
    # we still pass those.
    replace_kwargs.update(changes)

    return dataclasses.replace(obj, **replace_kwargs)
