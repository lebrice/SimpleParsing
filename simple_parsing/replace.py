from __future__ import annotations

import logging
import warnings
from collections import OrderedDict
from dataclasses import MISSING, Field, fields
from typing import Mapping

from simple_parsing.helpers.serialization.serializable import from_dict, to_dict

from .utils import DataclassT, K, PossiblyNestedDict, V, dict_union

logger = logging.getLogger(__name__)


def unflatten_with_selection(
    flattened: Mapping[tuple[K, ...], V], dataclass_cls: DataclassT
) -> PossiblyNestedDict[K, V]:
    """Unflatten a dictionary back into a possibly nested dictionary that contains selection information"""
    flattened = {tuple(key.split(".")): value for key, value in flattened.items()}
    flattened = OrderedDict(sorted(flattened.items(), key=lambda k: len(k[0])))

    nested: PossiblyNestedDict[K, V] = {}
    nested_fields: dict[str, tuple[dict, Field]] = {f.name: ({}, f) for f in fields(dataclass_cls)}
    for keys, value in flattened.items():
        sub_dictionary = nested
        sub_fields = nested_fields

        for part in keys[:-1]:
            assert isinstance(sub_dictionary, dict)
            sub_dictionary = sub_dictionary.setdefault(part, {})
            sub_fields, cur_field = sub_fields[part]

            if cur_field.metadata.get("subgroups") and len(sub_fields) == 0:
                # TODO: Do we raise ValueError or just Warning when selection is not provided
                warnings.warn(
                    f"The choice of the subgroups '{part}' is not provided. We will use the default of the subgroups"
                )
                if cur_field.default is MISSING and cur_field.default_factory is MISSING:
                    raise ValueError(f"The choice of the subgroups '{part}' is not provided.")
                else:
                    sub_cls = cur_field.metadata["subgroups"][
                        cur_field.metadata["subgroup_default"]
                    ]
                    sub_fields[part] = ({f.name: ({}, f) for f in fields(sub_cls)}, cur_field)
        else:
            key = keys[-1]
            if key in sub_fields and sub_fields[key][1].metadata.get("subgroups"):
                _, my_field = sub_fields[key]
                if isinstance(value, str):
                    sub_cls = my_field.metadata["subgroups"][value]
                    sub_fields[key] = ({f.name: ({}, f) for f in fields(sub_cls)}, my_field)
                    sub_dictionary = sub_dictionary.setdefault(f"__subgroups__@{key}", value)
                else:
                    sub_dictionary[key] = value

            elif key.startswith(f"__subgroups__@"):
                list_splits = key.split("@")
                if len(list_splits) > 2 and len(list_splits) <= 1:
                    raise KeyError(f"Key '{key}' is in valid")
                real_key = list_splits[1]

                _, my_field = sub_fields[real_key]
                sub_cls = my_field.metadata["subgroups"][value]
                sub_fields[real_key] = ({f.name: ({}, f) for f in fields(sub_cls)}, my_field)
                sub_dictionary = sub_dictionary.setdefault(key, value)
            else:
                sub_dictionary[key] = value
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
    unflatten_new_values = unflatten_with_selection(new_values, dataclass)
    new_dataclass_dict = dict_union(dataclass_dict, unflatten_new_values, recurse=True)
    return from_dict(
        type(dataclass), new_dataclass_dict, drop_extra_fields=True, parse_selection=True
    )
