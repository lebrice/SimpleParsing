from dataclasses import dataclass
from typing import Optional

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
