from __future__ import annotations

import logging
from dataclasses import MISSING, fields, is_dataclass
import functools
from simple_parsing.helpers.serialization.serializable import from_dict, to_dict
from simple_parsing.utils import unflatten_split

from .utils import DataclassT, dict_union

logger = logging.getLogger(__name__)


def invoke_post_init_inplace(dataclass: DataclassT, recurse: bool = True) -> None:
    for f in fields(dataclass):
        if f.default_factory is not MISSING:
            if is_dataclass(f.default_factory) or \
                (
                    isinstance(f.default_factory, functools.partial) and \
                    is_dataclass(f.default_factory.func)
                ):
                    if recurse:
                        invoke_post_init_inplace(getattr(dataclass, f.name), recurse=recurse)
    
    if getattr(dataclass, "__post_init__", None):
        dataclass.__post_init__()

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

    dataclass_dict = to_dict(dataclass, recurse=True, add_selected_subgroups=True)
    unflatten_new_values = unflatten_split(new_values)
    new_dataclass_dict = dict_union(dataclass_dict, unflatten_new_values, recurse=True)
    replaced_dataclass = from_dict(
        type(dataclass), new_dataclass_dict, drop_extra_fields=True, parse_selection=True
    )
    invoke_post_init_inplace(replaced_dataclass)
    return replaced_dataclass