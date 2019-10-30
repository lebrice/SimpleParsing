import argparse
import dataclasses
import shlex
from dataclasses import dataclass, field
from typing import *

import pytest

from .testutils import TestSetup
from simple_parsing import (Formatter, InconsistentArgumentError,
                            ArgumentParser)

    
# call a test function multiple times passing in different arguments in turn.
# argvalues generally needs to be a list of values if argnames specifies only one name or a list of tuples of values if argnames specifies multiple names.
# Example: @parametrize('arg1', [1,2]) would lead to two calls of the decorated test function,
# one with arg1=1 and another with arg1=2.see https://docs.pytest.org/en/latest/parametrize.html for more info and examples.


@dataclass()
class ClassA():
    a: int = 1


@dataclass()
class ClassB():
    b: int = 2


@dataclass()
class ClassC():
    c: int = 3


@dataclass()
class Container1(TestSetup):
    v1: int = 0
    class_a: ClassA = ClassA()
    class_b: ClassB = ClassB()


@dataclass()
class Container2(TestSetup):
    list_of_class_c: List[ClassC] = field(default_factory=list)


xfail_nesting_isnt_supported_yet = pytest.mark.xfail(reason="TODO: make sure this is how people would want to use this feature.")

# @xfail_nesting_isnt_supported_yet
def test_nesting_no_args():
    c1 = Container1.setup("")
    assert c1.v1 == 0
    assert c1.class_a.a == 1
    assert c1.class_b.b == 2

# @xfail_nesting_isnt_supported_yet
def test_nesting_with_args():
    c1 = Container1.setup("--a 123 --b 456 --v1 3")
    assert c1.v1 == 3
    assert c1.class_a.a == 123
    assert c1.class_b.b == 456


@xfail_nesting_isnt_supported_yet
def test_nesting_with_containers_no_args():
    container = Container2.setup("")
    assert len(container.list_of_class_c) == 0


@xfail_nesting_isnt_supported_yet
def test_nesting_with_containers_with_args():
    container = Container2.setup("--c 1 2 3")
    assert len(container.list_of_class_c) == 3
    c1, c2, c3 = tuple(container.list_of_class_c)
    assert c1.c == 1
    assert isinstance(c1, ClassC)
    assert c2.c == 2
    assert isinstance(c2, ClassC)
    assert c3.c == 3
    assert isinstance(c3, ClassC)


@xfail_nesting_isnt_supported_yet
def test_nesting_multiple_containers_containers_no_args():
    container1, container2, container3 = Container2.setup_multiple(3, "--c '1 2' '3 4' '5 6'")
    assert len(container1.list_of_class_c) == 3
    c1, c2 = tuple(container1.list_of_class_c)
    assert c1.c == 1
    assert isinstance(c1, ClassC)
    assert c2.c == 2
    assert isinstance(c2, ClassC)


    assert len(container2.list_of_class_c) == 3
    c1, c2 = tuple(container2.list_of_class_c)
    assert c1.c == 3
    assert isinstance(c1, ClassC)
    assert c2.c == 4
    assert isinstance(c2, ClassC)

    assert len(container3.list_of_class_c) == 3
    c1, c2 = tuple(container3.list_of_class_c)
    assert c1.c == 5
    assert isinstance(c1, ClassC)
    assert c2.c == 6
    assert isinstance(c2, ClassC)