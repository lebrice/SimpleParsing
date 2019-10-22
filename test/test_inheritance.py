import argparse
import dataclasses
import shlex
from dataclasses import dataclass, field
from typing import *

import pytest

from simple_parsing import (Formatter, InconsistentArgumentError,
                            ParseableFromCommandLine)

from .testutils import TestSetup


@dataclass()
class Base(ParseableFromCommandLine, TestSetup):
    """ Some extension of base-class `Base` """
    common_attribute: int = 1


@dataclass()
class ExtendedA(Base):
    a: int = 2

@dataclass()
class ExtendedB(Base):
    b: int = 3


def setup(arguments=""):
    parser = argparse.ArgumentParser(formatter_class=Formatter)
    ExtendedA.add_arguments(parser)
    ExtendedB.add_arguments(parser)

    splits = shlex.split(arguments)
    args = parser.parse_args(splits)

    extb = ExtendedA.from_args(args)
    extc = ExtendedB.from_args(args)
    return extb, extc

@pytest.mark.xfail(reason="TODO: make sure this is how people would want to use this feature.")
def test_subclasses_with_same_base_class_no_args():
    ext_a, ext_b = setup()
    
    assert ext_a.common_attribute == 1
    assert ext_a.a == 2

    assert ext_b.common_attribute == 1
    assert ext_b.b == 3


@pytest.mark.xfail(reason="TODO: make sure this is how people would want to use this feature.")
def test_subclasses_with_same_base_class_with_args():
    ext_a, ext_b = setup("--a 10 --b 20 --a 30 --c 40")
    
    assert ext_a.common_attribute == 10
    assert ext_a.a == 20

    assert ext_b.common_attribute == 30
    assert ext_b.b == 40
