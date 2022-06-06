""" Tests for issue 144: https://github.com/lebrice/SimpleParsing/issues/144 """
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

import pytest

from simple_parsing.helpers.serialization.serializable import Serializable


class TestOptional:
    @dataclass
    class Foo(Serializable):
        foo: Optional[int] = 123

    @pytest.mark.parametrize("d", [{"foo": None}, {"foo": 1}])
    def test_round_trip(self, d: dict):
        # NOTE: this double round-trip makes the comparison agnostic to any conversion that may
        # happen between the raw dict values and the arguments of the dataclasses.
        assert self.Foo.from_dict(self.Foo.from_dict(d).to_dict()) == self.Foo.from_dict(d)


class TestUnion:
    @dataclass
    class Foo(Serializable):
        foo: Union[int, dict[int, bool]] = 123

    @pytest.mark.parametrize("d", [{"foo": None}, {"foo": {1: "False"}}])
    def test_round_trip(self, d: dict):
        # NOTE: this double round-trip makes the comparison agnostic to any conversion that may
        # happen between the raw dict values and the arguments of the dataclasses.
        assert self.Foo.from_dict(self.Foo.from_dict(d).to_dict()) == self.Foo.from_dict(d)


class TestList:
    @dataclass
    class Foo(Serializable):
        foo: List[int] = field(default_factory=list)

    @pytest.mark.parametrize("d", [{"foo": []}, {"foo": [123, 456]}])
    def test_round_trip(self, d: dict):
        # NOTE: this double round-trip makes the comparison agnostic to any conversion that may
        # happen between the raw dict values and the arguments of the dataclasses.
        assert self.Foo.from_dict(self.Foo.from_dict(d).to_dict()) == self.Foo.from_dict(d)


class TestTuple:
    @dataclass
    class Foo(Serializable):
        foo: Tuple[int, float, bool]

    @pytest.mark.parametrize("d", [{"foo": (1, 1.2, False)}, {"foo": ("1", "1.2", "True")}])
    def test_round_trip(self, d: dict):
        # NOTE: this double round-trip makes the comparison agnostic to any conversion that may
        # happen between the raw dict values and the arguments of the dataclasses.
        assert self.Foo.from_dict(self.Foo.from_dict(d).to_dict()) == self.Foo.from_dict(d)


class TestDict:
    @dataclass
    class Foo(Serializable):
        foo: Dict[int, float] = field(default_factory=dict)

    @pytest.mark.parametrize("d", [{"foo": {}}, {"foo": {"123": "4.56"}}])
    def test_round_trip(self, d: dict):
        # NOTE: this double round-trip makes the comparison agnostic to any conversion that may
        # happen between the raw dict values and the arguments of the dataclasses.
        assert self.Foo.from_dict(self.Foo.from_dict(d).to_dict()) == self.Foo.from_dict(d)
