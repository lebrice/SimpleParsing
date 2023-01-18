from __future__ import annotations

import logging

from simple_parsing.helpers.serialization.serializable import from_dict, to_dict

from .utils import DataclassT, dict_union, PossiblyNestedDict, K, V, unflatten_split
from typing import Mapping, Tuple, Dict, List
from dataclasses import fields, Field
from collections import OrderedDict

logger = logging.getLogger(__name__)


def unflatten_with_selection(flattened: Mapping[Tuple[K,...], V], dataclass_cls: DataclassT) -> PossiblyNestedDict[K,V]:
    """Unflatten a dictionary back into a possibly nested dictionary that contains selection information
    """
    flattened = {tuple(key.split('.')): value for key, value in flattened.items()}
    flattened = OrderedDict(sorted(flattened.items(), key=lambda k: len(k[0])))
    # flattened = OrderedDict(flattened)
    # sorted(flattened, key=lambda x: len())
    logger.info(flattened)
    nested: PossiblyNestedDict[K, V] = {}
    nested_fields: Dict[str, Tuple[Dict, Field]] = {f.name: ({}, f) for f in fields(dataclass_cls)}
    for keys, value in flattened.items():
        sub_dictionary = nested
        sub_fields = nested_fields
        
        for part in keys[:-1]:
            logger.info(f"[part] {part}")
            assert isinstance(sub_dictionary, dict)
            sub_dictionary = sub_dictionary.setdefault(part, {})
            sub_fields, cur_field = sub_fields[part]
            logger.info(f"{part} {sub_fields.keys()}")
            
            if cur_field.metadata.get("subgroups") and len(sub_fields) == 0:
                raise ValueError(f"The choice of the subgroups '{part}' is not provided.")
            logger.info(f"[sub_fields1] {sub_fields.keys()} {cur_field}")
            logger.info(f"[sub_dict1] {sub_dictionary}")
        else:
            key = keys[-1]
            logger.info(f"[key] {key} {sub_fields.keys()}")
            if key in sub_fields and sub_fields[key][1].metadata.get('subgroups'):
                _, my_field = sub_fields[key]
                if isinstance(value, str):
                    sub_cls = my_field.metadata.get("subgroups")[value]
                    sub_fields[key] = ({f.name: ({}, f) for f in fields(sub_cls)}, my_field)
                    logger.info(f"[sub_fields2] {sub_fields.keys()}")
                    logger.info(f"[sub_dict2] {sub_dictionary}")
                    sub_dictionary = sub_dictionary.setdefault(f"__subgroups__@{key}", value)
                
                else:
                    sub_dictionary[key] = value
                    logger.info(value)
            elif key.startswith(f"__subgroups__@"):
                logger.info(key)
                list_splits = key.split("@")
                if len(list_splits) > 2 and len(list_splits) <= 1:
                    raise KeyError(f"Key '{key}' is in valid")
                real_key = list_splits[1]
                logger.info(real_key)
                _, my_field = sub_fields[real_key]
                sub_cls = my_field.metadata.get("subgroups")[value]
                sub_fields[real_key] = ({f.name: ({}, f) for f in fields(sub_cls)}, my_field)
                sub_dictionary = sub_dictionary.setdefault(key, value)
                logger.info(f"[sub_fields3] {sub_fields.keys()}")
                logger.info(f"[sub_dict3] {sub_dictionary}")
            else:
                sub_dictionary[key] = value
    logger.info(nested)
    return nested

def unflatten_with_selection1(flattened: Mapping[Tuple[K,...], V], dataclass_cls: DataclassT) -> PossiblyNestedDict[K,V]:
    """Unflatten a dictionary back into a possibly nested dictionary
    """
    flattened = {tuple(key.split('.')): value for key, value in flattened.items()}
    logger.info(f"[flattened] {flattened}")
    nested: PossiblyNestedDict[K, V] = {}
    for keys, value in flattened.items():
        fields_dict = {f.name: f for f in fields(dataclass_cls)}
        logger.info(f"[keys_value] {keys} {value}")
        sub_dictionary = nested
        for i in range(len(keys)-1):
            part = keys[i]
            assert isinstance(sub_dictionary, dict)
            logger.info(f"[nested1] {nested}")
            sub_dictionary = sub_dictionary.setdefault(part, {})
        else:
            key = keys[-1]
            logger.info(f"[key] {key}")
            if key in fields_dict and fields_dict[key].metadata.get("subgroups"):
                sub_dictionary.setdefault(f"__subgroups__@{keys[0]}", value)
                logger.info(f"[nested2] {nested}")
                continue
            else:
                sub_dictionary[keys[-1]] = value
                logger.info(f"[nested3] {nested}")
    logger.info(f'[nested4] {nested}')
    return nested

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

    dataclass_dict = to_dict(dataclass, recurse=True, add_selection=True)
    logger.info(dataclass_dict)
    unflatten_new_values = unflatten_with_selection(new_values_dict, dataclass)
    # unflatten_new_values = unflatten_split(new_values_dict)
    logger.info(unflatten_new_values)
    new_dataclass_dict = dict_union(dataclass_dict, unflatten_new_values, recurse=True)
    logger.info(new_dataclass_dict)
    return from_dict(
        type(dataclass), new_dataclass_dict, drop_extra_fields=True, parse_selection=True
    )
