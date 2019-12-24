import shlex
from dataclasses import dataclass

import pytest

from simple_parsing import ArgumentParser

from .testutils import *


@dataclass
class Base(TestSetup):
    """ Some extension of base-class `Base` """
    common_attribute: int = 1

@dataclass
class ExtendedA(Base):
    a: int = 2

@dataclass
class ExtendedB(Base):
    b: int = 3


def inheritance_setup(arguments=""):
    parser = ArgumentParser()
    parser.add_arguments(ExtendedA, "extended_a")
    parser.add_arguments(ExtendedB, "extended_b")

    splits = shlex.split(arguments)
    args = parser.parse_args(splits)

    exta = args.extended_a
    extb = args.extended_b
    return exta, extb

def test_simple_subclassing_no_args():
    extended = ExtendedA.setup()
    assert extended.a == 2
    assert extended.common_attribute == 1


def test_simple_subclassing_with_args():
    extended = ExtendedA.setup("--common_attribute 123 --a 56")
    assert extended.a == 56
    assert extended.common_attribute == 123
    

@xfail(reason="TODO: make sure this is how people would want to use this feature.")
def test_subclasses_with_same_base_class_no_args():
    ext_a, ext_b = inheritance_setup()
    
    assert ext_a.common_attribute == 1
    assert ext_a.a == 2

    assert ext_b.common_attribute == 1
    assert ext_b.b == 3


@xfail(reason="TODO: make sure this is how people would want to use this feature.")
def test_subclasses_with_same_base_class_with_args():
    ext_a, ext_b = inheritance_setup("--a 10 --b 20 --a 30 --c 40")
    
    assert ext_a.common_attribute == 10
    assert ext_a.a == 20

    assert ext_b.common_attribute == 30
    assert ext_b.b == 40