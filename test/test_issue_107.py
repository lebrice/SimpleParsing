"""Test for https://github.com/lebrice/SimpleParsing/issues/107."""
from dataclasses import dataclass
from typing import Any

import pytest

from simple_parsing.helpers.serialization.serializable import Serializable


@dataclass
class Foo(Serializable):
    a: bool = False


@pytest.mark.parametrize(
    "passed, expected",
    [
        ("True", True),
        ("False", False),
        (True, True),
        (False, False),
        ("true", True),
        ("false", False),
        ("1", True),
        ("0", False),
        (1, True),
        (0, False),
    ],
)
def test_parsing_of_bool_works_as_expected(passed: Any, expected: bool):
    assert Foo.from_dict({"a": passed}) == Foo(a=expected)
