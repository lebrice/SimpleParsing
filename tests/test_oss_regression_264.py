import warnings
from dataclasses import dataclass
from typing import Union

import pytest

from simple_parsing import Serializable


@pytest.mark.parametrize(
    "annotation",
    [
        Union[float, bool],
        Union[bool, float],
        Union[float, bool, None],
        Union[bool, float, None],
    ],
    ids=["float-bool", "bool-float", "optional-float-bool", "optional-bool-float"],
)
@pytest.mark.parametrize("value", [False, True, 0.0, 1.0, 2.5])
def test_numeric_boolean_union_json_round_trip(annotation, value, tmp_path):
    @dataclass
    class Options(Serializable):
        value: annotation = False

    path = tmp_path / "options.json"
    Options(value=value).save(path)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        loaded = Options.load(path)

    assert type(loaded.value) is type(value)
    assert loaded.value == value
    assert not caught
