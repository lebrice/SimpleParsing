from __future__ import annotations

import copy
import dataclasses
import logging
from typing import Any, overload, Mapping

from simple_parsing.annotation_utils.get_field_annotations import (
    get_field_type_from_annotations,
)
from simple_parsing.helpers.subgroups import Key
from simple_parsing.utils import (
    DataclassT,
    contains_dataclass_type_arg,
    is_dataclass_instance,
    is_dataclass_type,
    is_optional,
    is_union,
    PossiblyNestedDict,
    V,
    unflatten_split
)

logger = logging.getLogger(__name__)



def unflatten_selection_dict(
    flattened: Mapping[str, V], keyword: str = "__key__", sep="."
) -> PossiblyNestedDict[str, V]:
    """
    This function convert a flattened dict into a nested dict
    and it inserts the `keyword` as the selection into the nested dict.

    >>> unflatten_selection_dict({'ab_or_cd': 'cd', 'ab_or_cd.c_or_d': 'd'})
    {'ab_or_cd': {'__key__': 'cd', 'c_or_d': 'd'}}

    >>> unflatten_selection_dict({"a": 1, "b": 2})
    {'a': {'__key__': 1}, 'b': {'__key__': 2}}
    """
    dc = {}
    for k, v in flattened.items():
        if keyword != k and sep not in k and not isinstance(v, dict):
            dc[k + sep + keyword] = v
        else:
            dc[k] = v
    logger.debug(dc)
    return unflatten_split(dc)


@overload
def replace_subgroups(
    obj: DataclassT,
    changes_dict: dict[str, Any],
    selections: dict[str, Key | DataclassT] | None = None,
) -> DataclassT:
    ...


@overload
def replace_subgroups(
    obj: DataclassT, selections: dict[str, Key | DataclassT] | None = None, **changes
) -> DataclassT:
    ...


def replace_subgroups(
    obj: DataclassT, selections: dict[str, Key | DataclassT] | None = None
):
    """
    This function replaces the dataclass of subgroups, union, and optional union.
    The `selections` dict can be in flat format or in nested format.

    The values of selections can be `Key` of subgroups, dataclass type, and dataclass instance.
    """
    keyword = "__key__"

    if selections:
        selections = unflatten_selection_dict(selections, keyword)
    else:
        return obj

    replace_kwargs = {}
    for field in dataclasses.fields(obj):
        if field.name not in selections:
            continue

        field_value = getattr(obj, field.name)
        t = get_field_type_from_annotations(obj.__class__, field.name)
        
        new_value = None
        # Replace subgroup is allowed when the type annotation contains dataclass
        if contains_dataclass_type_arg(t):
            child_selections = selections.pop(field.name)
            key = child_selections.pop(keyword, None)

            if is_dataclass_type(key):
                field_value = key()
                logger.debug("is_dataclass_type")
            elif is_dataclass_instance(key):
                field_value = copy.deepcopy(key)
                logger.debug("is_dataclass_instance")
            elif field.metadata.get("subgroups", None):
                field_value = field.metadata["subgroups"][key]()
                logger.debug("is_subgroups")
            elif is_optional(t) and key is None:
                field_value = None
                logger.debug("key is None")
            elif contains_dataclass_type_arg(t) and key is None:
                field_value = field.default_factory()
                logger.debug(f"nested_dataclass")
            else:
                raise ValueError(f"invalid selection key '{key}' for field '{field.name}'")

            if child_selections:
                new_value = replace_subgroups(field_value, child_selections)
            else:
                new_value = field_value
        else:
            raise ValueError(f"The replaced subgroups contains no dataclass in its annotation {t}")
            
        if not field.init:
            raise ValueError(f"Cannot replace value of non-init field {field.name}.")

        replace_kwargs[field.name] = new_value
    return dataclasses.replace(obj, **replace_kwargs)