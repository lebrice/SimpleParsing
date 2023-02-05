from __future__ import annotations

import copy
import dataclasses
import logging
from typing import Any, overload

from simple_parsing.annotation_utils.get_field_annotations import (
    get_field_type_from_annotations,
)
from simple_parsing.helpers.subgroups import Key
from simple_parsing.replace import replace
from simple_parsing.utils import (
    DataclassT,
    contains_dataclass_type_arg,
    is_dataclass_instance,
    is_dataclass_type,
    is_optional,
    is_union,
    unflatten_keyword,
)

logger = logging.getLogger(__name__)


@overload
def replace_selections(
    obj: DataclassT,
    changes_dict: dict[str, Any],
    selections: dict[str, Key | DataclassT] | None = None,
) -> DataclassT:
    ...


@overload
def replace_selections(
    obj: DataclassT, selections: dict[str, Key | DataclassT] | None = None, **changes
) -> DataclassT:
    ...


def replace_selected_dataclass(
    obj: DataclassT, selections: dict[str, Key | DataclassT] | None = None
):
    """
    This function replaces the dataclass of subgroups, union, and optional union.
    The `selections` is in flat format, e.g. {"ab_or_cd": 'cd', "ab_or_cd.c_or_d": 'd'}

    The values of selections can be `Key` of subgroups, dataclass type, and dataclass instance.
    """
    keyword = "__key__"

    if selections:
        selections = unflatten_keyword(selections, keyword)
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
            else:
                raise ValueError(f"invalid selection key '{key}' for field '{field.name}'")

            if child_selections:
                new_value = replace_selected_dataclass(field_value, child_selections)
            else:
                new_value = field_value

            if not field.init:
                raise ValueError(f"Cannot replace value of non-init field {field.name}.")

        replace_kwargs[field.name] = new_value
    return dataclasses.replace(obj, **replace_kwargs)


def replace_selections(
    obj: DataclassT,
    changes_dict: dict[str, Any] | None = None,
    selections: dict[str, Key | DataclassT] | None = None,
    **changes,
) -> DataclassT:
    """Replace some values in a dataclass and replace dataclass type in nested union of dataclasses or subgroups.

    Compared to `simple_replace.replace`, this calls `replace_selected_dataclass` before calling `simple_parsing.replace`.

    ## Examples
    >>> import dataclasses
    >>> from simple_parsing import replace_selections, subgroups
    >>> from typing import Union
    >>> @dataclasses.dataclass
    ... class A:
    ...     a: int = 0
    >>> @dataclasses.dataclass
    ... class B:
    ...     b: str = "b"
    >>> @dataclasses.dataclass
    ... class Config:
    ...     a_or_b: Union[A, B] = subgroups({'a': A, 'b': B}, default_factory=A)
    ...     a_or_b_union: Union[A, B] = dataclasses.field(default_factory=A)
    ...     a_optional: Union[A, None] = None

    >>> base_config = Config(a_or_b=A(a=1))
    >>> replace_selections(base_config, {"a_or_b.b": "bob"}, {"a_or_b": "b"})
    Config(a_or_b=B(b='bob'), a_or_b_union=A(a=0), a_optional=None)

    >>> replace_selections(base_config, {"a_or_b_union.b": "bob"}, {"a_or_b_union": B})
    Config(a_or_b=A(a=1), a_or_b_union=B(b='bob'), a_optional=None)

    >>> replace_selections(base_config, {"a_optional.a": 2}, {"a_optional": A})
    Config(a_or_b=A(a=1), a_or_b_union=A(a=0), a_optional=A(a=2))
    """
    if selections:
        obj = replace_selected_dataclass(obj, selections)
    return replace(obj, changes_dict, **changes)
