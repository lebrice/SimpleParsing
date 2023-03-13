import json
from dataclasses import dataclass
from test.testutils import Generic, TypeVar
from typing import Any, Dict, List, Literal, Optional, Tuple, Type

import pytest
import warnings

from simple_parsing.helpers import Serializable, dict_field, list_field
from simple_parsing.helpers.serialization.decoding import get_decoding_fn


def test_encode_something(simple_attribute):

    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass(Serializable):
        d: Dict[str, some_type] = dict_field()
        l: List[Tuple[some_type, some_type]] = list_field()
        t: Dict[str, Optional[some_type]] = dict_field()
        # w: Dict[str, Union[some_type, int, str, None, str, None]] = dict_field()

    b = SomeClass()
    b.d.update({"hey": expected_value})
    b.l.append((expected_value, expected_value))
    b.t.update({"hey": None, "hey2": expected_value})
    # b.w.update({
    #     "hey": None,
    #     "hey2": "heyo",
    #     "hey3": 1,
    #     "hey4": expected_value,
    # })
    assert SomeClass.loads(b.dumps()) == b


def test_literal_decoding():
    @dataclass
    class SomeClass(Serializable):
        x: Literal["a", "b", "c"] = "a"

    # This test should fail if there's a warning on decoding- previous versions
    # have raised a UserWarning when decoding a literal, of the form:
    # Unable to find a decoding function for annotation typing.Literal['a', 'b', 'c']
    with warnings.catch_warnings():
        warnings.simplefilter("error")

        assert SomeClass.loads('{"x": "a"}') == SomeClass()

    # Make sure that we can't decode a value that's not in the literal
    with pytest.raises(TypeError):
        SomeClass.loads('{"x": "d"}')


def test_typevar_decoding(simple_attribute):
    @dataclass
    class Item(Serializable, decode_into_subclasses=True):
        name: str = "chair"
        price: float = 399
        stock: int = 10

    @dataclass
    class DiscountedItem(Item):
        discount_factor: float = 0.5

    ItemT = TypeVar("ItemT", bound=Item)

    @dataclass
    class Container(Serializable, Generic[ItemT]):
        items: List[ItemT] = list_field()

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
    b.d.update({"hey": expected_value})
    b.l.append((expected_value, expected_value))
    b.t.update({"hey": None, "hey2": expected_value})
    # b.w.update({
    #     "hey": None,
    #     "hey2": "heyo",
    #     "hey3": 1,
    #     "hey4": expected_value,
    # })
    assert SomeClass.loads(b.dumps()) == b


def test_super_nesting():
    @dataclass
    class Complicated(Serializable):
        x: List[List[List[Dict[int, Tuple[int, float, str, List[float]]]]]] = list_field()

    c = Complicated()
    c.x = [[[{0: (2, 1.23, "bob", [1.2, 1.3])}]]]
    assert Complicated.loads(c.dumps()) == c
    assert c.dumps() == '{"x": [[[{"0": [2, 1.23, "bob", [1.2, 1.3]]}]]]}'


@pytest.mark.parametrize(
    "some_type, encoded_value, expected_value",
    [
        # (Tuple[int, float], json.loads(json.dumps([1, 2])), (1, 2.0)),
        (
            List[Tuple[int, float]],
            json.loads(json.dumps([[1, 2], [3, 4]])),
            [(1, 2.0), (3, 4.0)],
        ),
    ],
)
def test_decode_tuple(some_type: Type, encoded_value: Any, expected_value: Any):
    decoding_function = get_decoding_fn(some_type)
    actual = decoding_function(encoded_value)
    assert actual == expected_value
