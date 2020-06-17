"""Adds typed dataclasses for the "config" yaml files.
"""
import json
import textwrap
from collections import OrderedDict
from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional, Tuple, Mapping, Type
from pathlib import Path
import pytest

from simple_parsing import mutable_field
from simple_parsing.helpers import Serializable, YamlSerializable
from test.conftest import silent
import yaml
import json

SerializableBase = Serializable

# Test both json and yaml serialization.
for Serializable in (Serializable, YamlSerializable):
    SerializableBase.subclasses.clear()
    
    @dataclass
    class Child(Serializable):
        name: str = "bob"
        age: int = 10

    @dataclass
    class Parent(Serializable):
        name: str = "Consuela"
        children: Dict[str, Child] = mutable_field(OrderedDict)


    def test_to_dict(silent):
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

    def test_loads_dumps(silent):
        bob = Child("Bob")
        clarice = Child("Clarice")
        nancy = Parent("Nancy", children=dict(bob=bob, clarice=clarice))
        assert Parent.loads(nancy.dumps()) == nancy 


    def test_load_dump(silent, tmpdir: Path):
        bob = Child("Bob")
        clarice = Child("Clarice")
        nancy = Parent("Nancy", children=dict(bob=bob, clarice=clarice))
        tmp_path = tmpdir / "tmp"
        with open(tmp_path, "w") as fp:
            nancy.dump(fp)
        with open(tmp_path, "r") as fp:
            assert Parent.load(fp) == nancy 


    @dataclass
    class ParentWithOptionalChildren(Parent):
        name: str = "Consuela"
        children: Dict[str, Optional[Child]] = mutable_field(OrderedDict)


    def test_optionals(silent):
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
        assert ParentWithOptionalChildren.loads(nancy.dumps()) == nancy 

    @dataclass
    class ChildWithFriends(Child):
        friends: List[Optional[Child]] = mutable_field(list)


    @dataclass
    class ParentWithOptionalChildrenWithFriends(Serializable):
        name: str = "Consuela"
        children: Mapping[str, Optional[ChildWithFriends]] = mutable_field(OrderedDict)


    def test_lists(silent):
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

        s = nancy.dumps()
        parsed_nancy = ParentWithOptionalChildrenWithFriends.loads(s)
        assert isinstance(parsed_nancy.children["bob"], ChildWithFriends), parsed_nancy.children["bob"]
        
        assert parsed_nancy == nancy

    @dataclass
    class Base(Serializable, decode_into_subclasses=True):
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
    class Container(Serializable):
        items: List[Base] = field(default_factory=list)

    def test_decode_right_subclass(silent):
        c = Container()
        c.items.append(Base())
        c.items.append(A())
        c.items.append(B())
        val = c.dumps()
        parsed_val = Container.loads(val)
        assert c == parsed_val


    def test_forward_ref_dict(silent):
        @dataclass
        class LossWithDict(Serializable):
            name: str = ""
            total: float = 0.
            sublosses: Dict[str, "LossWithDict"] = field(default_factory=OrderedDict)

        recon = LossWithDict(name="recon", total=1.2)
        kl = LossWithDict(name="kl", total=3.4)
        test = LossWithDict(name="test", total=recon.total + kl.total, sublosses={"recon":recon, "kl":kl})
        assert LossWithDict.loads(test.dumps()) == test

    def test_forward_ref_list(silent):
            
        @dataclass
        class JLossWithList(Serializable):
            name: str = ""
            total: float = 0.
            same_level: List["JLossWithList"] = field(default_factory=list)

        recon = JLossWithList(name="recon", total=1.2)
        kl = JLossWithList(name="kl", total=3.4)
        test = JLossWithList(name="test", total=recon.total + kl.total, same_level=[kl])
        assert JLossWithList.loads(test.dumps()) == test


    def test_forward_ref_attribute():
        @dataclass
        class LossWithAttr(Serializable):
            name: str = ""
            total: float = 0.
            attribute: Optional["LossWithAttr"] = None

        recon = LossWithAttr(name="recon", total=1.2)
        kl = LossWithAttr(name="kl", total=3.4)
        test = LossWithAttr(name="test", total=recon.total + kl.total, attribute=recon)
        assert LossWithAttr.loads(test.dumps()) == test


    @dataclass
    class Loss(Serializable):
        bob: str = "hello"


    def test_forward_ref_correct_one_chosen_if_two_types_have_same_name():
        @dataclass
        class Loss(Serializable):
            name: str = ""
            total: float = 0.
            sublosses: Dict[str, "Loss"] = field(default_factory=OrderedDict)
            fofo: int = 1
        
        recon = Loss(name="recon", total=1.2)
        kl = Loss(name="kl", total=3.4)
        test = Loss(name="test", total=recon.total + kl.total, sublosses={"recon":recon,"kl":kl}, fofo=123)
        assert Loss.loads(test.dumps(), drop_extra_fields=False) == test



    def test_nested_list():
        @dataclass
        class Kitten(Serializable):
            name: str = "Meow"

        @dataclass
        class Cat(Serializable):
            name: str = "bob"
            age: int = 12
            litters: List[List[Kitten]] = field(default_factory=list)

        kittens: List[List[Kitten]] = [
            [
                Kitten(name=f"kitten_{i}") for i in range(i*5, i*5 + 5)
            ]
            for i in range(2)
        ]
        mom = Cat("Chloe", age=12, litters=kittens)
        
        assert Cat.loads(mom.dumps()) == mom


    def test_nested_list_optional():
        @dataclass
        class Kitten(Serializable):
            name: str = "Meow"

        @dataclass
        class Cat(Serializable):
            name: str = "bob"
            age: int = 12
            litters: List[List[Optional[Kitten]]] = field(default_factory=list)

        kittens: List[List[Optional[Kitten]]] = [
            [
                (Kitten(name=f"kitten_{i}") if i % 2 == 0 else None) for i in range(i*5, i*5 + 5)
            ]
            for i in range(2)
        ]
        mom = Cat("Chloe", age=12, litters=kittens)
        
        assert Cat.loads(mom.dumps()) == mom


    def test_dicts():
        @dataclass
        class Cat:
            name: str
            age: int = 1

        @dataclass
        class Bob(Serializable):
            cats: Dict[str, Cat] = mutable_field(dict)

        bob = Bob(cats={"Charlie": Cat("Charlie", 1)})
        assert Bob.loads(bob.dumps()) == bob

        d = bob.to_dict()
        assert Bob.from_dict(d) == bob
