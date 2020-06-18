import shlex
from dataclasses import dataclass

import pytest

from simple_parsing import ArgumentParser
from simple_parsing.helpers import Serializable, list_field, choice
from .testutils import *


@dataclass
class Base(TestSetup):
    """ Some extension of base-class `Base` """
    a: int = 1

@dataclass
class ExtendedB(Base, TestSetup):
    b: int = 2

@dataclass
class ExtendedC(Base, TestSetup):
    c: int = 3


@dataclass
class Inheritance(TestSetup):
    ext_b: ExtendedB = ExtendedB()
    ext_c: ExtendedC = ExtendedC()


def test_simple_subclassing_no_args():
    extended = ExtendedB.setup()
    assert extended.a == 1
    assert extended.b == 2


def test_simple_subclassing_with_args():
    extended = ExtendedB.setup("--a 123 --b 56")
    assert extended.a == 123
    assert extended.b == 56
    

# @xfail(reason="TODO: make sure this is how people would want to use this feature.")
def test_subclasses_with_same_base_class_no_args():
    ext = Inheritance.setup()
    
    assert ext.ext_b.a == 1
    assert ext.ext_b.b == 2

    assert ext.ext_c.a == 1
    assert ext.ext_c.c == 3


def test_subclasses_with_same_base_class_with_args():
    ext = Inheritance.setup(
        "--ext_b.a 10 --b 20 --ext_c.a 30 --c 40",
        conflict_resolution_mode=ConflictResolution.AUTO
    )
    assert ext.ext_b.a == 10
    assert ext.ext_b.b == 20

    assert ext.ext_c.a == 30
    assert ext.ext_c.c == 40


@xfail(reason=(
    "Merging is not working yet with triangle inheritance, since we wouldn't "
    "know how to assign which value to which attribute..")
)
def test_subclasses_with_same_base_class_with_args_merge():
    ext = Inheritance.setup(
        "--a 10 30 --b 20 --c 40",
        conflict_resolution_mode=ConflictResolution.ALWAYS_MERGE
    )
    
    assert ext.ext_b.a == 10
    assert ext.ext_b.b == 20

    assert ext.ext_c.a == 30
    assert ext.ext_c.c == 40

def test_weird_structure():
    """both is-a, and has-a at the same time, a very weird inheritance structure
    """
        
    @dataclass
    class ConvBlock(Serializable):
        """A Block of Conv Layers."""
        n_layers: int = 4  # number of layers
        n_filters: List[int] = list_field(16, 32, 64, 64)  # filters per layer
        

    @dataclass
    class GeneratorHParams(ConvBlock):
        """Settings of the Generator model"""
        conv: ConvBlock = ConvBlock()
        optimizer: str = choice("ADAM", "RMSPROP", "SGD", default="ADAM")
        

    @dataclass
    class DiscriminatorHParams(ConvBlock):
        """Settings of the Discriminator model"""
        conv: ConvBlock = ConvBlock()
        optimizer: str = choice("ADAM", "RMSPROP", "SGD", default="ADAM")

    @dataclass
    class SomeWeirdClass(TestSetup):
        gen: GeneratorHParams
        disc: DiscriminatorHParams
    
    s = SomeWeirdClass.setup()
    assert s.gen.conv.n_layers == 4
    assert s.gen.n_layers == 4
    assert s.disc.conv.n_layers == 4
    assert s.disc.n_layers == 4
    