from __future__ import annotations

import logging

from simple_parsing.helpers.serialization.serializable import from_dict, to_dict

from .utils import DataclassT, dict_union, unflatten_split

logger = logging.getLogger(__name__)


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
    unflatten_new_values = unflatten_split(new_values_dict)
    new_dataclass_dict = dict_union(dataclass_dict, unflatten_new_values, recurse=True)
    logger.info(new_dataclass_dict)
    return from_dict(
        type(dataclass), new_dataclass_dict, drop_extra_fields=True, parse_selection=True
    )
