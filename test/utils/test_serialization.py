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
from simple_parsing.helpers.serialization import JsonSerializableFlexible as JsonSerializable


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



def test_forward_ref_dict():

        
    @dataclass
    class LossWithDict(JsonSerializable):
        name: str = ""
        total: float = 0.
        sublosses: Dict[str, "LossWithDict"] = field(default_factory=OrderedDict)

    recon = LossWithDict(name="recon", total=1.2)
    kl = LossWithDict(name="kl", total=3.4)
    test = LossWithDict(name="test", total=recon.total + kl.total, sublosses={"recon":recon,"kl":kl})
    assert LossWithDict.loads(test.dumps()) == test




def test_forward_ref_list():
        
    @dataclass
    class LossWithList(JsonSerializable):
        name: str = ""
        total: float = 0.
        same_level: List["LossWithList"] = field(default_factory=list)

    recon = LossWithList(name="recon", total=1.2)
    kl = LossWithList(name="kl", total=3.4)
    test = LossWithList(name="test", total=recon.total + kl.total, same_level=[kl])
    assert LossWithList.loads(test.dumps()) == test



def test_forward_ref_attribute():
    @dataclass
    class LossWithAttr(JsonSerializable):
        name: str = ""
        total: float = 0.
        attribute: Optional["LossWithAttr"] = None

    recon = LossWithAttr(name="recon", total=1.2)
    kl = LossWithAttr(name="kl", total=3.4)
    test = LossWithAttr(name="test", total=recon.total + kl.total, attribute=recon)
    assert LossWithAttr.loads(test.dumps()) == test



@dataclass
class Loss(JsonSerializable):
    bob: str = "hello"


def test_forward_ref_correct_one_chosen_if_two_types_have_same_name():
        
    @dataclass
    class Loss(JsonSerializable):
        name: str = ""
        total: float = 0.
        sublosses: Dict[str, "Loss"] = field(default_factory=OrderedDict)
        fofo: int = 1
    
    recon = Loss(name="recon", total=1.2)
    kl = Loss(name="kl", total=3.4)
    test = Loss(name="test", total=recon.total + kl.total, sublosses={"recon":recon,"kl":kl}, fofo=123)
    assert Loss.loads(test.dumps(), drop_extra_fields=False) == test
