import shlex
from dataclasses import dataclass

import pytest

from simple_parsing import ArgumentParser

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


# @xfail(reason="TODO: make sure this is how people would want to use this feature.")
def test_subclasses_with_same_base_class_with_args():
    ext = Inheritance.setup("--ext_b.a 10 --ext_b.b 20 --ext_c.a 30 --ext_c.c 40", conflict_resolution_mode=ConflictResolution.AUTO)
    
    assert ext.ext_b.a == 10
    assert ext.ext_b.b == 20

    assert ext.ext_c.a == 30
    assert ext.ext_c.c == 40


@xfail(reason="TODO: merging is not working yet with triangle inheritance, because we are merging the two classes, instead of merging the fields.")
def test_subclasses_with_same_base_class_with_args_merge():
    ext = Inheritance.setup(
        "--a 10 30 --b 20 --c 40",
        conflict_resolution_mode=ConflictResolution.ALWAYS_MERGE
    )
    
    assert ext.ext_b.a == 10
    assert ext.ext_b.b == 20

    assert ext.ext_c.a == 30
    assert ext.ext_c.c == 40