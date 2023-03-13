import json
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from test.testutils import Generic, TypeVar
from typing import Any, Dict, List, Optional, Tuple, Type

import pytest

from simple_parsing.helpers import Serializable, dict_field, list_field
from simple_parsing.helpers.serialization.decoding import (
    get_decoding_fn,
    register_decoding_fn,
)


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


@dataclass
class Hparams:
    use_log: int = 1
    severity: int = 2
    probs: List[int] = field(default_factory=lambda: [1, 2])


@dataclass
class Parameters(Serializable):
    hparams: Hparams = field(default_factory=Hparams)


def test_implicit_int_casting(tmp_path: Path):
    """Test for 'issue' #227: https://github.com/lebrice/SimpleParsing/issues/227"""

    with open(tmp_path / "conf.yaml", "w") as f:
        f.write(
            textwrap.dedent(
                """\
                hparams:
                    use_log: 1
                    severity: 0.1
                    probs: [0.1, 0.2]
                """
            )
        )

    file_config = Parameters.load(tmp_path / "conf.yaml")
    assert file_config == Parameters(hparams=Hparams(severity=0, probs=[0, 0]))


def test_registering_safe_casting_decoding_fn():
    """Test the solution to 'issue' #227: https://github.com/lebrice/SimpleParsing/issues/227"""

    # Solution: register a decoding function for `int` that casts to int, but raises an error if
    # the value would lose precision.

    # Do this so the parsing function for `List[int]` is rebuilt to use the new parsing function
    # for `int`.
    get_decoding_fn.cache_clear()

    def _safe_cast(v: Any) -> int:
        int_v = int(v)
        if int_v != float(v):
            raise ValueError(f"Cannot safely cast {v} to int")
        return int_v

    register_decoding_fn(int, _safe_cast, overwrite=True)

    assert (
        Parameters.loads_yaml(
            textwrap.dedent(
                """\
        hparams:
            use_log: 1
            severity: 0.0
            probs: [3, 4.0]
        """
            )
        )
        == Parameters(hparams=Hparams(severity=0, probs=[3, 4]))
    )

    with pytest.raises(ValueError, match="Cannot safely cast 0.1 to int"):
        Parameters.loads_yaml(
            textwrap.dedent(
                """\
            hparams:
                use_log: 1
                severity: 0.1
                probs: [0, 0]
            """
            )
        )

    with pytest.raises(ValueError, match="Cannot safely cast 0.2 to int"):
        Parameters.loads_yaml(
            textwrap.dedent(
                """\
            hparams:
                use_log: 1
                severity: 1
                probs: [0.2, 0.3]
            """
            )
        )

    register_decoding_fn(int, int, overwrite=True)


@pytest.mark.xfail(strict=True, match="DID NOT RAISE <class 'ValueError'>")
def test_optional_list_type_doesnt_use_type_decoding_fn():
    """BUG: Parsing an Optional[list[int]] doesn't work correctly."""

    # Do this so the parsing function for `List[int]` is rebuilt to use the new parsing function
    # for `int`.
    get_decoding_fn.cache_clear()

    def _safe_cast(v: Any) -> int:
        int_v = int(v)
        if int_v != float(v):
            raise ValueError(f"Cannot safely cast {v} to int")
        return int_v

    register_decoding_fn(int, _safe_cast, overwrite=True)

    with pytest.raises(ValueError):
        get_decoding_fn(List[int])([0.1, 0.2])

    # BUG: This doesn't work correctly.
    with pytest.raises(ValueError):
        get_decoding_fn(Optional[List[int]])([0.1, 0.2])

    register_decoding_fn(int, int, overwrite=True)
