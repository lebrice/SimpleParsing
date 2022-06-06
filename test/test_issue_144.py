""" Tests for issue 144: https://github.com/lebrice/SimpleParsing/issues/144 """
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union

from simple_parsing.helpers.serialization.serializable import Serializable


@dataclass
class Foo(Serializable):
    bar: Optional[int] = 123


class TestOptional:
    def test_deserialize(self):
        foo = Foo.from_dict({"bar": None})
        assert foo == Foo(bar=None)

    def test_serialize(self):
        foo = Foo.from_dict({"bar": None})
        assert foo == Foo(bar=None)


@dataclass
class Bar(Serializable):
    a: Union[int, dict[int, bool]] = 123


class TestUnion:
    def test_deserialize(self):
        assert Bar.from_dict({"a": 1}) == Bar(a=1)
        assert Bar.from_dict({"a": {1: True}}) == Bar(a={1: True})

    def test_serialize(self):
        assert Bar.from_dict({"a": 1}) == Bar(a=1)
        assert Bar.from_dict({"a": {1: True}}) == Bar(a={1: True})
