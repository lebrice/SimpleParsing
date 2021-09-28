import pytest

from dataclasses import dataclass
from simple_parsing import ArgumentParser, choice
from typing import Union
from .testutils import *


@dataclass
class A(TestSetup):
    color: str = choice("red", "green", "blue", default="red")
    colors: List[str] = choice("red", "green", "blue", default_factory=["red"].copy)


def test_choice_default():
    a = A.setup("")
    assert a.color == "red"
    assert a.colors == ["red"]


def test_value_not_in_choices_throws_error():
    with raises(SystemExit):
        a = A.setup("--color orange")
    with raises(SystemExit):
        A.setup("--colors red orange")


def test_passed_value_works_fine():
    a = A.setup("--color red")
    assert a.color == "red"

    a = A.setup("--color green")
    assert a.color == "green"

    a = A.setup("--color blue")
    assert a.color == "blue"

    a = A.setup("--colors red blue")
    assert a.colors == ["red", "blue"]

    a = A.setup("--colors blue red green red")
    assert a.colors == ["blue", "red", "green", "red"]


@dataclass
class Base:
    value: str = "hello base"


@dataclass
class AA(Base):
    value: str = "hello a"


@dataclass
class BB(Base):
    value: str = "hello b"


def test_choice_with_dict():
    @dataclass
    class C(TestSetup):
        option: Union[AA, BB, float] = choice(
            {"a": AA("aaa"), "b": BB("bbb"), "bob": AA("bobobo"), "f": 1.23},
            default="a",
        )
        options: List[Union[AA, BB, float]] = choice(
            {"a": AA("aaa"), "b": BB("bbb"), "bob": AA("bobobo"), "f": 1.23},
            default_factory=["a"].copy,
        )

    c = C.setup("")
    assert c.option == AA("aaa")
    assert c.options == [AA("aaa")]

    c = C.setup("--option a --options a a")
    assert c.option == AA("aaa")
    assert c.options == [AA("aaa"), AA("aaa")]

    c = C.setup("--option bob --options bob a")
    assert c.option == AA("bobobo")
    assert c.options == [AA("bobobo"), AA("aaa")]

    c = C.setup("--option f --options a f a b")
    assert c.option == 1.23
    assert c.options == [AA("aaa"), 1.23, AA("aaa"), BB("bbb")]


def test_choice_with_default_instance():
    @dataclass
    class D(TestSetup):
        option: Union[AA, BB, float] = choice(
            {
                "a": [AA("aa1"), AA("aa2")],
                "b": 1.23,
                "bob": BB("bobobo"),
            },
            default="a",
        )

    @dataclass
    class Parent(TestSetup):
        d: D = D(option=AA("parent"))

    p = Parent.setup("")
    assert p.d.option == AA("parent")


from enum import Enum


class Color(Enum):
    blue: str = "BLUE"
    red: str = "RED"
    green: str = "GREEN"
    orange: str = "ORANGE"


def test_passing_enum_to_choice():
    @dataclass
    class Something(TestSetup):
        favorite_color: Color = choice(Color, default=Color.green)
        colors: List[Color] = choice(Color, default_factory=[Color.green].copy)

    s = Something.setup("")
    assert s.favorite_color == Color.green
    assert s.colors == [Color.green]

    s = Something.setup("--colors blue red")
    assert s.colors == [Color.blue, Color.red]


def test_passing_enum_to_choice_no_default_makes_required_arg():
    @dataclass
    class Something(TestSetup):
        favorite_color: Color = choice(Color)

    with raises(SystemExit):
        s = Something.setup("")

    s = Something.setup("--favorite_color blue")
    assert s.favorite_color == Color.blue


def test_passing_enum_to_choice_with_key_as_default():
    with pytest.warns(UserWarning):

        @dataclass
        class Something(TestSetup):
            favorite_color: Color = choice(Color, default="blue")


def test_passing_enum_to_choice_is_same_as_enum_attr():
    @dataclass
    class Something1(TestSetup):
        favorite_color: Color = Color.orange

    @dataclass
    class Something2(TestSetup):
        favorite_color: Color = choice(Color, default=Color.orange)

    s1 = Something1.setup("--favorite_color green")
    s2 = Something2.setup("--favorite_color green")
    assert s1.favorite_color == s2.favorite_color

    s = Something1.setup("--favorite_color blue")
    assert s.favorite_color == Color.blue
    s = Something2.setup("--favorite_color blue")
    assert s.favorite_color == Color.blue
