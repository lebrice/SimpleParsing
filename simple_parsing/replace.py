from __future__ import annotations

import copy
import dataclasses
import logging
from typing import Any, Mapping, overload

from simple_parsing.annotation_utils.get_field_annotations import (
    get_field_type_from_annotations,
)
from simple_parsing.helpers.subgroups import Key
from simple_parsing.utils import (
    DataclassT,
    PossiblyNestedDict,
    V,
    contains_dataclass_type_arg,
    is_dataclass_instance,
    is_dataclass_type,
    is_optional,
    unflatten_split,
)

logger = logging.getLogger(__name__)


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


def replace_subgroups(
    obj: DataclassT, selections: dict[str, Key | DataclassT] | None = None
) -> DataclassT:
    """This function replaces the dataclass of subgroups, union, and optional union. The
    `selections` dict can be in flat format or in nested format.

    The values of selections can be `Key` of subgroups, dataclass type, and dataclass instance.
    """
    keyword = "__key__"

    if not selections:
        return obj
    selections = _unflatten_selection_dict(selections, keyword, recursive=False)

    replace_kwargs = {}
    for field in dataclasses.fields(obj):
        if not field.init:
            raise ValueError(f"Cannot replace value of non-init field {field.name}.")

        if field.name not in selections:
            continue

        field_value = getattr(obj, field.name)
        field_annotation = get_field_type_from_annotations(obj.__class__, field.name)

        new_value = None
        # Replace subgroup is allowed when the type annotation contains dataclass
        if not contains_dataclass_type_arg(field_annotation):
            raise ValueError(
                f"The replaced subgroups contains no dataclass in its annotation {field_annotation}"
            )

        selection = selections.pop(field.name)
        if isinstance(selection, dict):
            value_of_selection = selection.pop(keyword, None)
            child_selections = selection
        else:
            value_of_selection = selection
            child_selections = None

        if is_dataclass_type(value_of_selection):
            field_value = value_of_selection()
        elif is_dataclass_instance(value_of_selection):
            field_value = copy.deepcopy(value_of_selection)
        elif field.metadata.get("subgroups", None):
            assert isinstance(value_of_selection, str)
            subgroup_selection = field.metadata["subgroups"][value_of_selection]
            if is_dataclass_instance(subgroup_selection):
                # when the subgroup selection is a frozen dataclass instance
                field_value = subgroup_selection
            else:
                # when the subgroup selection is a dataclass type
                field_value = field.metadata["subgroups"][value_of_selection]()
        elif is_optional(field_annotation) and value_of_selection is None:
            field_value = None
        elif contains_dataclass_type_arg(field_annotation) and value_of_selection is None:
            field_value = field.default_factory()
        else:
            raise ValueError(
                f"invalid selection key '{value_of_selection}' for field '{field.name}'"
            )

        if child_selections:
            new_value = replace_subgroups(field_value, child_selections)
        else:
            new_value = field_value

        replace_kwargs[field.name] = new_value
    return dataclasses.replace(obj, **replace_kwargs)


def _unflatten_selection_dict(
    flattened: Mapping[str, V], keyword: str = "__key__", sep: str = ".", recursive: bool = True
) -> PossiblyNestedDict[str, V]:
    """This function convert a flattened dict into a nested dict and it inserts the `keyword` as
    the selection into the nested dict.

    >>> _unflatten_selection_dict({'ab_or_cd': 'cd', 'ab_or_cd.c_or_d': 'd'})
    {'ab_or_cd': {'__key__': 'cd', 'c_or_d': 'd'}}

    >>> _unflatten_selection_dict({'lv1': 'a', 'lv1.lv2': 'b', 'lv1.lv2.lv3': 'c'})
    {'lv1': {'__key__': 'a', 'lv2': {'__key__': 'b', 'lv3': 'c'}}}

    >>> _unflatten_selection_dict({'lv1': 'a', 'lv1.lv2': 'b', 'lv1.lv2.lv3': 'c'}, recursive=False)
    {'lv1': {'__key__': 'a', 'lv2': 'b', 'lv2.lv3': 'c'}}

    >>> _unflatten_selection_dict({'ab_or_cd.c_or_d': 'd'})
    {'ab_or_cd': {'c_or_d': 'd'}}

    >>> _unflatten_selection_dict({"a": 1, "b": 2})
    {'a': 1, 'b': 2}
    """
    dc = {}

    unflatten_those_top_level_keys = set()
    for k, v in flattened.items():
        splited_keys = k.split(sep)
        if len(splited_keys) >= 2:
            unflatten_those_top_level_keys.add(splited_keys[0])

    for k, v in flattened.items():
        keys = k.split(sep)
        top_level_key = keys[0]
        rest_keys = keys[1:]
        if top_level_key in unflatten_those_top_level_keys:
            sub_dc = dc.get(top_level_key, {})
            if len(rest_keys) == 0:
                sub_dc[keyword] = v
            else:
                sub_dc[".".join(rest_keys)] = v
            dc[top_level_key] = sub_dc
        else:
            dc[k] = v

    if recursive:
        for k in unflatten_those_top_level_keys:
            v = dc.pop(k)
            unflatten_v = _unflatten_selection_dict(v, recursive=recursive)
            dc[k] = unflatten_v
    return dc
