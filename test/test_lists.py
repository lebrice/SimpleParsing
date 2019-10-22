import argparse
import contextlib
import dataclasses
import inspect
import textwrap
from dataclasses import dataclass, field
from enum import Enum
from typing import *

import pytest

import simple_parsing
from simple_parsing import InconsistentArgumentError, ParseableFromCommandLine

from .testutils import TestSetup


@dataclass()
class ContainerClass(ParseableFromCommandLine, TestSetup):
    a: Tuple[int]
    b: List[int]
    c: Tuple[str] = field(default_factory=tuple)
    d: List[int] = field(default_factory=list)


def test_single_element_list():
    args = ContainerClass.setup("--a 1 --b 4 --c 7 --d 10")
    container = ContainerClass.from_args(args)
    assert container.a == (1,)
    assert container.b == [4]
    assert container.c == ('7',)
    assert container.d == [10]


def test_single_list_without_quotes_works():
    args = ContainerClass.setup("--a 1 2 3 --b 4 5 6 --c 7 8 9 --d 10 11 12")
    container = ContainerClass.from_args(args)
    assert container.a == (1, 2, 3)
    assert container.b == [4, 5, 6]
    assert container.c == ('7', '8', '9')
    assert container.d == [10, 11, 12]

   
    args = ContainerClass.setup("--a 1 2 --b 2 --c 3 4 5 --d 10 11 12")
    container = ContainerClass.from_args(args)
    assert container.a == (1,2)
    assert container.b == [2]
    assert container.c == ('3', '4', '5')
    assert container.d == [10, 11, 12]


def test_required_attributes_works():
    args = None
    with contextlib.suppress(SystemExit), pytest.raises(argparse.ArgumentError):
        args = ContainerClass.setup("--b 4")
    assert args is None

    with contextlib.suppress(SystemExit), pytest.raises(argparse.ArgumentError):
        args = ContainerClass.setup("--a 4")
    assert args is None

    args = ContainerClass.setup("--a 4 --b 5")
    assert args


def test_list_multiple_work_with_quotes():
    args = ContainerClass.setup("""--a '1 2 3' '4 5 6' --b "4 5 6" "7 8 9" --c "7 8 9" "7 9 11" --d '10 11 12'""", multiple=True)
    containers = ContainerClass.from_args_multiple(args, 2)
    container1 = containers[0]
    container2 = containers[1]
    assert container1.a == (1, 2, 3)
    assert container1.b == [4, 5, 6]
    assert container1.c == ('7', '8', '9')
    assert container1.d == [10, 11, 12]

    assert container2.a == (4, 5, 6)
    assert container2.b == [7, 8, 9]
    assert container2.c == ('7', '9', '11')
    assert container2.d == [10, 11, 12]

def test_list_multiple_work_with_brackets():
    args = ContainerClass.setup("""--a [1,2,3] [4,5,6] --b [4,5,6] [7,8,9] --c [7,8,9] [7,9,11] --d [10,11,12]""", multiple=True)
    containers = ContainerClass.from_args_multiple(args, 2)
    container1 = containers[0]
    container2 = containers[1]
    assert container1.a == (1, 2, 3)
    assert container1.b == [4, 5, 6]
    assert container1.c == ('7', '8', '9')
    assert container1.d == [10, 11, 12]

    assert container2.a == (4, 5, 6)
    assert container2.b == [7, 8, 9]
    assert container2.c == ('7', '9', '11')
    assert container2.d == [10, 11, 12]


@pytest.mark.xfail(reason="Supporting both this syntax and regular argparse syntax is kinda hard, and I'm not sure if it's needed.")
def test_single_list_with_quotes_works():
    args = ContainerClass.setup("""--a '1 2 3' --b "4 5 6" --c "7 9 11" --d '10 11 12'""")
    container = ContainerClass.from_args(args)
    assert container.a == (1, 2, 3)
    assert container.b == [4, 5, 6]
    assert container.c == ('7', '9', '11')
    assert container.d == [10, 11, 12]


@pytest.mark.xfail(reason="Supporting both this syntax and regular argparse syntax is kinda hard, and I'm not sure if it's needed.")
def test_single_list_with_brackets_works():
    args = ContainerClass.setup("""--a [1,2,3] --b [4,5,6] --c [7,9,11] --d [10,11,12]""")
    container = ContainerClass.from_args(args)
    assert container.a == (1, 2, 3)
    assert container.b == [4, 5, 6]
    assert container.c == ('7', '9', '11')
    assert container.d == [10, 11, 12]

# print(Container.get_help_text())
ContainerClass