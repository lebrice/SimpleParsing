from dataclasses import dataclass, field
from typing import List, Optional

import pytest
from simple_parsing import ArgumentParser

from .testutils import TestSetup


@dataclass
class Config:
    seed: Optional[int] = None

def test_optional_seed():
    """Test that a value marked as Optional works fine.
    
    (Reproduces https://github.com/lebrice/SimpleParsing/issues/14#issue-562538623)
    """
    parser = ArgumentParser()
    parser.add_arguments(Config, dest="config")

    args = parser.parse_args("".split())
    config: Config = args.config
    assert config == Config()

    args = parser.parse_args("--seed 123".split())
    config: Config = args.config
    assert config == Config(123)


@dataclass
class Child:
    name: str = "Kevin"
    age: int = 12


@dataclass
class Dog:
    breed: str = "Saint Bernard"
    dog_years: int = 49


@dataclass
class Parent(TestSetup):
    child: Optional[Child] = None
    dog: Optional[Dog] = None


def test_optional_parameter_group():
    """ Reproduces issue #28 :
    https://github.com/lebrice/SimpleParsing/issues/28#issue-663689719
    """
    parent: Parent = Parent.setup("--breed Shitzu")
    assert parent.dog == Dog(breed="Shitzu")
    assert parent.child == None

    parent: Parent = Parent.setup("--name Dylan")
    assert parent.dog == None
    assert parent.child == Child(name="Dylan")

    parent: Parent = Parent.setup("--name Dylan --dog_years 27")
    assert parent.dog == Dog(dog_years=27)
    assert parent.child == Child(name="Dylan")


@dataclass
class GrandParent(TestSetup):
    niece: Optional[Parent] = None
    nefew: Optional[Parent] = None


@pytest.mark.xfail(reason="TODO: Deeper nesting doesn't work atm!")
def test_deeply_nested_optional_parameter_groups():
    """ Same as above test, but deeper hierarchy.
    """
    grandparent: GrandParent = GrandParent.setup()
    assert grandparent.niece == None
    assert grandparent.nefew == None

    grandparent: GrandParent = GrandParent.setup("--niece.child.name Bob")
    assert grandparent.niece == Parent(child=Child(name="Bob"))
    assert grandparent.nefew == None


def test_optional_int():
    @dataclass
    class Bob(TestSetup):
        num_workers: Optional[int] = 12
  
    assert Bob.setup("--num_workers") == Bob(num_workers=None)
    # assert Bob.setup("--num_workers None") == Bob(num_workers=None)
    assert Bob.setup("--num_workers 123") == Bob(num_workers=123)
    # assert Bob.setup("--num_workers none") == Bob(num_workers=None)


def test_optional_str():
    @dataclass
    class Bob(TestSetup):
        a: Optional[str] = "123"
  
    assert Bob.setup("--a") == Bob(a=None)
    # assert Bob.setup("--a None") == Bob(a="None")
    assert Bob.setup("--a 123") == Bob(a="123")
    # assert Bob.setup("--a none") == Bob(a="none")


@pytest.mark.xfail(reason=f"TODO: Rework the code to parse containers.")
def test_optional_list_of_ints():
    @dataclass
    class Bob(TestSetup):
        a: Optional[List[int]] = field(default_factory=list)
  
    # assert Bob.setup("--a") == Bob(a=None)
    assert Bob.setup("--a 1") == Bob(a=[1])
    assert Bob.setup("--a 1 2 3") == Bob(a=[1, 2, 3])
    assert Bob.setup("--a []") == Bob(a=[])
    assert Bob.setup("") == Bob(a=[])
    # assert Bob.setup("--a None") == Bob(a=None)
    # assert Bob.setup("--a none") == Bob(a=None)


def test_optional_without_default():
    @dataclass
    class Bob(TestSetup):
        a: Optional[int]
    
    assert Bob.setup("") == Bob(a=None)
    assert Bob.setup("--a") == Bob(a=None)
    # assert Bob.setup("--a None") == Bob(a=None)
    assert Bob.setup("--a 123") == Bob(a=123)
    # assert Bob.setup("--a none") == Bob(a=None)
    
    

# def test_simple_optional_argument(simple_attribute, silent):
#     some_type, passed_value, expected_value = simple_attribute
#     @dataclass
#     class SomeDataclass(TestSetup):
#         some_attribute: Optional[some_type] # type: ignore
    
#     actual = SomeDataclass.setup(f"--some_attribute {passed_value}")
#     assert actual.some_attribute == expected_value
#     assert isinstance(actual.some_attribute, some_type)
