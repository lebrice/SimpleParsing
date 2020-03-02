import pytest

from dataclasses import dataclass
from simple_parsing import ArgumentParser, choice
from typing import Union
from .testutils import *

@dataclass
class A(TestSetup):
    color: str = choice("red", "green", "blue", default="red")



def test_choice_default():
    a = A.setup("")
    assert a.color == "red"


def test_value_not_in_choices_throws_error():
    with raises(argparse.ArgumentError):
        a = A.setup("--color orange")

def test_passed_value_works_fine():
    a = A.setup("--color red")
    assert a.color == "red"

    a = A.setup("--color green")
    assert a.color == "green"

    a = A.setup("--color blue")
    assert a.color == "blue"



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
        option: Union[AA, BB] = choice({
            "a": AA("aaa"),
            "b": BB("bbb"),
            "bob": AA("bobobo"),
        }, default="a")
    c = C.setup("--option a")
    assert c.option.value == "aaa"

    c = C.setup("--option bob")
    assert c.option.value == "bobobo"

def test_choice_with_dict_weird():
    @dataclass
    class D(TestSetup):
        option: List[Base] = choice({
            "a": [AA("aa1"), AA("aa2")],
            "b": 1.23,
            "bob": BB("bobobo"),
        }, default="a")
    c = D.setup("--option a")
    assert c.option == [AA("aa1"), AA("aa2")]

    c = D.setup("--option b")
    assert c.option == 1.23
    
    c = D.setup("--option bob")
    assert c.option == BB("bobobo")


def test_choice_with_default_instance():
    @dataclass
    class D(TestSetup):
        option: Union[AA, BB, float] = choice({
            "a": [AA("aa1"), AA("aa2")],
            "b": 1.23,
            "bob": BB("bobobo"),
        }, default="a")

    @dataclass
    class Parent(TestSetup):
        d: D = D(option=AA("parent"))


    p = Parent.setup("")
    assert p.d.option == AA("parent")
