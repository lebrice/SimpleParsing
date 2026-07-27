import json
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from test.testutils import Generic, TypeVar
from typing import Any, Optional, Union

import pytest
from typing_extensions import Literal

from simple_parsing.helpers import Serializable, dict_field, list_field
from simple_parsing.helpers.serialization.decoding import (
    get_decoding_fn,
    register_decoding_fn,
)
from simple_parsing.helpers.serialization.serializable import loads_json
from simple_parsing.utils import DataclassT

from .testutils import needs_yaml


def test_encode_something(simple_attribute):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass(Serializable):
        d: dict[str, some_type] = dict_field()  # pyright: ignore[reportInvalidTypeForm]
        some_list: list[tuple[some_type, some_type]] = list_field()  # pyright: ignore[reportInvalidTypeForm]
        t: dict[str, Optional[some_type]] = dict_field()  # pyright: ignore[reportInvalidTypeForm]
        # w: Dict[str, Union[some_type, int, str, None, str, None]] = dict_field()

    b = SomeClass()
    b.d.update({"hey": expected_value})
    b.some_list.append((expected_value, expected_value))
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
    # with pytest.warns(UserWarning, match="Unable to find a decoding function"):
    #     assert SomeClass.loads('{"x": "a"}') == SomeClass()

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
        items: list[ItemT] = list_field()

    chair = Item()
    cheap_chair = DiscountedItem(name="Cheap chair")
    c = Container(items=[chair, cheap_chair])

    assert Container.loads(c.dumps()) == c

    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass(Serializable):
        d: dict[str, some_type] = dict_field()  # pyright: ignore[reportInvalidTypeForm]
        some_list: list[tuple[some_type, some_type]] = list_field()  # pyright: ignore[reportInvalidTypeForm]
        t: dict[str, Optional[some_type]] = dict_field()  # pyright: ignore[reportInvalidTypeForm]
        # w: Dict[str, Union[some_type, int, str, None, str, None]] = dict_field()

    b = SomeClass()
    b.d.update({"hey": expected_value})
    b.some_list.append((expected_value, expected_value))
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
        x: list[list[list[dict[int, tuple[int, float, str, list[float]]]]]] = list_field()

    c = Complicated()
    c.x = [[[{0: (2, 1.23, "bob", [1.2, 1.3])}]]]
    assert Complicated.loads(c.dumps()) == c
    assert c.dumps() == '{"x": [[[{"0": [2, 1.23, "bob", [1.2, 1.3]]}]]]}'


@pytest.mark.parametrize(
    "some_type, encoded_value, expected_value",
    [
        # (Tuple[int, float], json.loads(json.dumps([1, 2])), (1, 2.0)),
        (
            list[tuple[int, float]],
            json.loads(json.dumps([[1, 2], [3, 4]])),
            [(1, 2.0), (3, 4.0)],
        ),
        (Union[int, float], "1", 1),
        (Union[int, float], "1.2", 1.2),
        pytest.param(
            Union[int, float],
            1.2,
            1.2,
            marks=[
                pytest.mark.xfail(reason="decoding an int works (but raises a warning)"),
            ],
        ),
        # NOTE: Here we expect a float, since it's the first type that will work.
        (Union[float, int], "1", 1.0),
        (Union[float, int], "1.2", 1.2),
        (Union[float, int], 1.2, 1.2),
    ],
)
def test_decode(some_type: type, encoded_value: Any, expected_value: Any):
    decoding_function = get_decoding_fn(some_type)
    actual = decoding_function(encoded_value)
    assert actual == expected_value
    assert type(actual) == type(expected_value)


@dataclass
class Hparams:
    use_log: int = 1
    severity: int = 2
    probs: list[int] = field(default_factory=lambda: [1, 2])


@dataclass
class Parameters(Serializable):
    hparams: Hparams = field(default_factory=Hparams)


def test_implicit_int_casting(tmp_path: Path):
    """Test that we do in fact perform the unsafe casting as described in #227:

    https://github.com/lebrice/SimpleParsing/issues/227
    """
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
    _yaml = pytest.importorskip("yaml")
    with pytest.warns(RuntimeWarning, match="Unsafe casting"):
        file_config = Parameters.load(tmp_path / "conf.yaml")
    assert file_config == Parameters(hparams=Hparams(severity=0, probs=[0, 0]))


@pytest.fixture(autouse=True)
def reset_int_decoding_fns_after_test():
    """Reset the decoding function for `int` to the default after each test."""
    from simple_parsing.helpers.serialization.decoding import _decoding_fns

    backup = _decoding_fns.copy()
    yield
    for key, value in _decoding_fns.items():
        if key not in backup:
            # print(f"Test added a decoding function for {key} with value {value}.")
            pass
        elif value != backup[key]:
            # print(
            #     f"Test changed the decoding function for {key} from {backup[key]} to {value}.",
            # )
            pass
    _decoding_fns.clear()
    _decoding_fns.update(backup)


@needs_yaml
def test_registering_safe_casting_decoding_fn():
    """Test the solution to 'issue' #227: https://github.com/lebrice/SimpleParsing/issues/227."""

    # Solution: register a decoding function for `int` that casts to int, but raises an error if
    # the value would lose precision.

    def _safe_cast(v: Any) -> int:
        int_v = int(v)
        if int_v != float(v):
            raise ValueError(f"Cannot safely cast {v} to int")
        return int_v

    register_decoding_fn(int, _safe_cast, overwrite=True)

    assert Parameters.loads_yaml(
        textwrap.dedent(
            """\
        hparams:
            use_log: 1
            severity: 0.0
            probs: [3, 4.0]
        """
        )
    ) == Parameters(hparams=Hparams(severity=0, probs=[3, 4]))

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


@pytest.mark.xfail(strict=True, match="DID NOT RAISE <class 'ValueError'>")
def test_optional_list_type_doesnt_use_type_decoding_fn():
    """BUG: Parsing an Optional[list[int]] doesn't work correctly."""

    def _safe_cast(v: Any) -> int:
        int_v = int(v)
        if int_v != float(v):
            raise ValueError(f"Cannot safely cast {v} to int")
        return int_v

    register_decoding_fn(int, _safe_cast, overwrite=True)

    with pytest.raises(ValueError):
        get_decoding_fn(list[int])([0.1, 0.2])

    # BUG: This doesn't work correctly.
    with pytest.raises(ValueError):
        get_decoding_fn(Optional[list[int]])([0.1, 0.2])


@dataclass
class ClassWithInt:
    a: int = 1


@dataclass
class ClassWithIntList:
    values: list[int] = field(default_factory=[1, 2, 3].copy)


@pytest.mark.parametrize(
    ("class_to_use", "serialized_dict", "expected_message", "expected_result"),
    [
        pytest.param(
            ClassWithInt,
            {"a": 1.1},
            r"Unsafe casting occurred when deserializing field 'a' of type <class 'int'>: raw value: 1.1, decoded value: 1",
            ClassWithInt(a=int(1.1)),
            id="float to int",
        ),
        pytest.param(
            ClassWithInt,
            {"a": True},
            r"Unsafe casting occurred when deserializing field 'a' of type <class 'int'>: raw value: True, decoded value: 1",
            ClassWithInt(a=int(True)),
            id="bool to int",
        ),
        pytest.param(
            ClassWithIntList,
            {"values": [1.1, 2.2, 3.3]},
            r"Unsafe casting occurred when deserializing field 'values' of type list\[int\]: raw value: \[1.1, 2.2, 3.3\], decoded value: \[1, 2, 3\].",
            ClassWithIntList(values=[int(1.1), int(2.2), int(3.3)]),
            id="List of floats",
        ),
    ],
)
def test_issue_227_unsafe_int_casting_on_load(
    class_to_use: type[DataclassT],
    serialized_dict: dict,
    expected_message: str,
    expected_result: DataclassT,
):
    """Test that a warning is raised when performing a lossy cast when deserializing a
    dataclass."""
    with pytest.warns(
        RuntimeWarning,
        match=expected_message,
    ) as record:
        obj = loads_json(class_to_use, json.dumps(serialized_dict))
        assert obj == expected_result
    assert len(record.list) == 1
