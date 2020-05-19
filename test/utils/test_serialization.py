"""Adds typed dataclasses for the "config" yaml files.
"""
import json
import textwrap
from collections import OrderedDict
from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional, Tuple, Mapping
from pathlib import Path
import pytest

from simple_parsing import mutable_field
from simple_parsing.helpers import JsonSerializable


@dataclass
class Child(JsonSerializable):
    name: str = "bob"
    age: int = 10

@dataclass
class Parent(JsonSerializable):
    name: str = "Consuela"
    children: Dict[str, Child] = mutable_field(OrderedDict)


def test_to_dict():
    bob = Child("Bob")
    clarice = Child("Clarice")
    nancy = Parent("Nancy", children=dict(bob=bob, clarice=clarice))

    assert nancy.to_dict() == {
        "name": "Nancy",
        "children": {
            "bob": {"name": "Bob", "age": 10},
            "clarice": {"name": "Clarice", "age": 10}
        },
    }


def test_loads_dumps():
    bob = Child("Bob")
    clarice = Child("Clarice")
    nancy = Parent("Nancy", children=dict(bob=bob, clarice=clarice))

    assert Parent.loads(nancy.dumps()) == nancy 


@dataclass
class ParentWithOptionalChildren(Parent):
    name: str = "Consuela"
    children: Dict[str, Optional[Child]] = mutable_field(OrderedDict)


def test_optionals():
    bob = Child("Bob")
    clarice = Child("Clarice")
    nancy = ParentWithOptionalChildren("Nancy", children=dict(bob=bob, clarice=clarice))
    nancy.children["jeremy"] = None
    assert nancy.to_dict() == {
        "name": "Nancy",
        "children": {
            "bob": {"name": "Bob", "age": 10},
            "clarice": {"name": "Clarice", "age": 10},
            "jeremy": None,
        },
    }
    # print(f"all available subclasses: {JsonSerializable.subclasses}")
    assert ParentWithOptionalChildren.loads(nancy.dumps()) == nancy 


@dataclass
class ChildWithFriends(Child):
    friends: List[Optional[Child]] = mutable_field(list)


@dataclass
class ParentWithOptionalChildrenWithFriends(JsonSerializable):
    name: str = "Consuela"
    children: Mapping[str, Optional[ChildWithFriends]] = mutable_field(OrderedDict)


def test_lists():
    bob = ChildWithFriends("Bob")
    clarice = Child("Clarice")
    
    bob.friends.append(clarice)
    bob.friends.append(None)

    nancy = ParentWithOptionalChildrenWithFriends("Nancy", children=dict(bob=bob))    
    nancy.children["jeremy"] = None

    assert nancy.to_dict() == {
        "name": "Nancy",
        "children": {
            "bob": {"name": "Bob", "age": 10, "friends": [
                {"name": "Clarice", "age": 10},
                None,
            ]},
            "jeremy": None,
        },
    }

    dumps = nancy.dumps()
    parsed_nancy = ParentWithOptionalChildrenWithFriends.loads(dumps)
    assert isinstance(parsed_nancy.children["bob"], ChildWithFriends), parsed_nancy.children["bob"]
    
    assert parsed_nancy == nancy

@dataclass
class Base(JsonSerializable, decode_into_subclasses=True):
    name: str = "bob"


@dataclass
class A(Base):
    name: str = "A"
    age: int = 123

@dataclass
class B(Base):
    name: str = "B"
    favorite_color: str = "blue"

@dataclass
class Container(JsonSerializable):
    items: List[Base] = field(default_factory=list)

def test_decode_right_subclass():
    c = Container()
    c.items.append(Base())
    c.items.append(A())
    c.items.append(B())
    val = c.dumps()
    parsed_val = Container.loads(val)
    assert c == parsed_val
