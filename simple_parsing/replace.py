from __future__ import annotations

import dataclasses
from typing import Any, overload, Mapping
import copy

from simple_parsing.annotation_utils.get_field_annotations import (
    get_field_type_from_annotations,
)
from simple_parsing.helpers.subgroups import Key
from simple_parsing.utils import DataclassT, is_dataclass_instance, unflatten_split
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
            elif is_dataclass_instance(key):
                field_value = copy.deepcopy(key)
            elif field.metadata.get("subgroups", None):
                field_value = field.metadata["subgroups"][key]()
            elif is_optional(t) and key is None:
                field_value = None
            elif contains_dataclass_type_arg(t) and key is None:
                field_value = field.default_factory()
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