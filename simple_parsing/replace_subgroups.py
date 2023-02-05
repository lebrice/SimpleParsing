from __future__ import annotations
import dataclasses
from simple_parsing.utils import is_dataclass_instance, DataclassT, unflatten_split, contains_dataclass_type_arg, is_dataclass_type, is_union, is_optional
from typing import Any, overload, Union, Tuple
from simple_parsing.helpers.subgroups import Key
from enum import Enum
from simple_parsing.annotation_utils.get_field_annotations import get_field_type_from_annotations
from simple_parsing.replace import replace
import logging
import copy

logger = logging.getLogger(__name__)

def unflatten_subgroup_changes(subgroup_changes: dict[str, Key]):
    """
    This function convert subgroup_changes = {"ab_or_cd": "cd", "ab_or_cd.c_or_d": "d"}
    into {"ab_or_cd": {"__key__": "cd", "c_or_d": {"__key__": "d"}}}
    """
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
    
   
def replace_union_dataclasses(obj: DataclassT, selections: dict[str, Key|DataclassT] | None = None):
    if selections:
        selections = unflatten_subgroup_changes(selections)
    else:
        return obj
    
    replace_kwargs = {}
    for field in dataclasses.fields(obj):
        if field.name not in selections:
            continue
            
        field_value = getattr(obj, field.name)
        t = get_field_type_from_annotations(obj.__class__, field.name)
        if contains_dataclass_type_arg(t) and is_union(t):
            child_selections = selections.pop(field.name)
            key = child_selections.pop("__key__", None)
            logger.debug(key)
            if is_dataclass_type(key):
                field_value = key()
                logger.debug('is_dataclass_type')
            elif is_dataclass_instance(key):
                field_value = copy.deepcopy(key)
                logger.debug('is_dataclass_instance')
            elif field.metadata.get("subgroups", None):
                field_value = field.metadata["subgroups"][key]()
                logger.debug('is_subgroups')
            elif is_optional(t) and key is None:
                field_value = None
                logger.debug("key is None")
            else:
                logger.debug('default')
            if child_selections:
                new_value = replace_union_dataclasses(field_value, child_selections)
            else:
                new_value = field_value
        replace_kwargs[field.name] = new_value
    
    return dataclasses.replace(obj, **replace_kwargs)
    
def replace_subgroups(obj: DataclassT, changes_dict: dict[str, Any] | None = None, subgroup_changes: dict[str, Key] | None = None, **changes) -> DataclassT:
    if subgroup_changes:
        obj = replace_union_dataclasses(obj, subgroup_changes)
    return replace(obj, changes_dict, **changes)

# def replace_subgroups(obj: DataclassT, changes_dict: dict[str, Any] | None = None, subgroup_changes: dict[str, Key] | None = None, **changes) -> DataclassT:
#     if changes_dict and changes:
#         raise ValueError("Cannot pass both `changes_dict` and `changes`")
#     changes = changes_dict or changes
#     # changes can be given in a 'flat' format in `changes_dict`, e.g. {"a.b.c": 123}.
#     # Unflatten them back to a nested dict (e.g. {"a": {"b": {"c": 123}}})
#     changes = unflatten_split(changes)

#     if subgroup_changes:
#         # subgroup_changes is in a flat format, e.g. {"ab_or_cd": 'cd', "ab_or_cd.c_or_d": 'd'}
#         subgroup_changes = unflatten_subgroup_changes(subgroup_changes)
        
#     replace_kwargs = {}
#     for field in dataclasses.fields(obj):
#         if field.name in changes:
#             if not field.init:
#                 raise ValueError(f"Cannot replace value of non-init field {field.name}.")

#             field_value = getattr(obj, field.name)

#             if is_dataclass_instance(field_value) and isinstance(changes[field.name], dict):
#                 field_changes = changes.pop(field.name)
#                 sub_subgroup_changes = None
#                 if subgroup_changes and field.name in subgroup_changes:
#                     sub_subgroup_changes = subgroup_changes.pop(field.name)
#                     key = sub_subgroup_changes.pop("__key__", None)
#                     if key and field.metadata.get('subgroups') and key in field.metadata['subgroups']:
#                         field_value = field.metadata['subgroups'][key]()
#                 new_value = replace_subgroups(field_value, field_changes, sub_subgroup_changes)
#             else:
#                 new_value = changes.pop(field.name)
#             replace_kwargs[field.name] = new_value
#         elif subgroup_changes and field.name in subgroup_changes:
#             if not field.init:
#                 raise ValueError(f"Cannot replace value of non-init field {field.name}.")
            
#             sub_subgroup_changes = subgroup_changes.pop(field.name)
#             key = sub_subgroup_changes.pop("__key__", None)
#             if key and field.metadata.get('subgroups') and key in field.metadata['subgroups']:
#                 field_value = field.metadata['subgroups'][key]()
#                 new_value = replace_subgroups(field_value, None, sub_subgroup_changes)
#             else:
#                 field_value = getattr(obj, field.name)
#                 new_value = replace_subgroups(field_value, None, sub_subgroup_changes)
#             replace_kwargs[field.name] = new_value
                
#     # note: there may be some leftover values in `changes` that are not fields of this dataclass.
#     # we still pass those.
#     replace_kwargs.update(changes)

#     return dataclasses.replace(obj, **replace_kwargs)
