
import json
import logging
import textwrap
from collections import OrderedDict
from dataclasses import dataclass, fields
from pathlib import Path
from test.conftest import silent
from test.testutils import *
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple, Type, Union

import pytest
import yaml

from simple_parsing import field, mutable_field
from simple_parsing.helpers import (Serializable, YamlSerializable, dict_field,
                                    list_field)
from simple_parsing.helpers.serialization.decoding import (
    _get_decoding_fn, register_decoding_fn)


def test_encode_something(simple_attribute):

    some_type, passed_value, expected_value = simple_attribute
    @dataclass
    class SomeClass(Serializable):
        d: Dict[str, some_type] = dict_field()
        l: List[Tuple[some_type, some_type]] = list_field()
        t: Dict[str, Optional[some_type]] = dict_field()
        # w: Dict[str, Union[some_type, int, str, None, str, None]] = dict_field()

    b = SomeClass()
    b.d.update({
        "hey": expected_value
    })
    b.l.append((expected_value, expected_value))
    b.t.update({
        "hey": None,
        "hey2": expected_value
    })
    # b.w.update({
    #     "hey": None,
    #     "hey2": "heyo",
    #     "hey3": 1,
    #     "hey4": expected_value,
    # })
    assert SomeClass.loads(b.dumps()) == b



def test_typevar_decoding(simple_attribute):
    
    @dataclass
    class Item(Serializable, decode_into_subclasses=True):
        name: str = "chair"
        price: float = 399
        stock: int = 10

    @dataclass
    class DiscountedItem(Item):
        discount_factor: float = 0.5

    I = TypeVar("I", bound=Item)

    @dataclass
    class Container(Serializable, Generic[I]):
        items: List[I] = list_field()


    chair = Item()
    cheap_chair = DiscountedItem(name="Cheap chair")
    c = Container(items=[chair, cheap_chair])

    assert Container.loads(c.dumps()) == c



    some_type, passed_value, expected_value = simple_attribute
    @dataclass
    class SomeClass(Serializable):
        d: Dict[str, some_type] = dict_field()
        l: List[Tuple[some_type, some_type]] = list_field()
        t: Dict[str, Optional[some_type]] = dict_field()
        # w: Dict[str, Union[some_type, int, str, None, str, None]] = dict_field()

    b = SomeClass()
    b.d.update({
        "hey": expected_value
    })
    b.l.append((expected_value, expected_value))
    b.t.update({
        "hey": None,
        "hey2": expected_value
    })
    # b.w.update({
    #     "hey": None,
    #     "hey2": "heyo",
    #     "hey3": 1,
    #     "hey4": expected_value,
    # })
    assert SomeClass.loads(b.dumps()) == b
