from contextlib import suppress
from argparse import ArgumentError
from dataclasses import dataclass, field
from typing import *

import pytest

import simple_parsing
from simple_parsing import ArgumentParser, InconsistentArgumentError

from .testutils import TestSetup


@dataclass()
class ContainerClass(TestSetup):
    a: Tuple[int]
    b: List[int]
    c: Tuple[str] = field(default_factory=tuple)
    d: List[int] = field(default_factory=list)


def test_single_element_list():
    container = ContainerClass.setup("--a 1 --b 4 --c 7 --d 10")
    assert container.a == (1,)
    assert container.b == [4]
    assert container.c == ('7',)
    assert container.d == [10]


def test_single_list_without_quotes_works():
    container = ContainerClass.setup("--a 1 2 3 --b 4 5 6 --c 7 8 9 --d 10 11 12")
    assert container.a == (1, 2, 3)
    assert container.b == [4, 5, 6]
    assert container.c == ('7', '8', '9')
    assert container.d == [10, 11, 12]

   
    container = ContainerClass.setup("--a 1 2 --b 2 --c 3 4 5 --d 10 11 12")
    assert container.a == (1,2)
    assert container.b == [2]
    assert container.c == ('3', '4', '5')
    assert container.d == [10, 11, 12]


def test_required_attributes_works():
    args = None
    with suppress(SystemExit), pytest.raises(ArgumentError):
        args = ContainerClass.setup("--b 4")
    assert args is None

    with suppress(SystemExit), pytest.raises(ArgumentError):
        args = ContainerClass.setup("--a 4")
    assert args is None

    args = ContainerClass.setup("--a 4 --b 5")
    assert args


def test_default_value():
    container = ContainerClass.setup("--a 1 2 3 --b 4 5 6")
    assert container.a == (1, 2, 3)
    assert container.b == [4, 5, 6]
    assert container.c == tuple()
    assert container.d == list()


def test_list_multiple_work_with_quotes():
    container1, container2 = ContainerClass.setup_multiple(2, """--a '1 2 3' '4 5 6' --b "4 5 6" "7 8 9" --c "7 8 9" "7 9 11" --d '10 11 12'""")
    assert container1.a == (1, 2, 3)
    assert container1.b == [4, 5, 6]
    assert container1.c == ('7', '8', '9')
    assert container1.d == [10, 11, 12]

    assert container2.a == (4, 5, 6)
    assert container2.b == [7, 8, 9]
    assert container2.c == ('7', '9', '11')
    assert container2.d == [10, 11, 12]

def test_list_multiple_work_with_brackets():
    container1, container2 = ContainerClass.setup_multiple(2, """--a [1,2,3] [4,5,6] --b [4,5,6] [7,8,9] --c [7,8,9] [7,9,11] --d [10,11,12]""", multiple=True)
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
    container = ContainerClass.setup("""--a '1 2 3' --b "4 5 6" --c "7 9 11" --d '10 11 12'""")
    assert container.a == (1, 2, 3)
    assert container.b == [4, 5, 6]
    assert container.c == ('7', '9', '11')
    assert container.d == [10, 11, 12]


@pytest.mark.xfail(reason="Supporting both this syntax and regular argparse syntax is kinda hard, and I'm not sure if it's needed.")
def test_single_list_with_brackets_works():
    container = ContainerClass.setup("""--a [1,2,3] --b [4,5,6] --c [7,9,11] --d [10,11,12]""")
    assert container.a == (1, 2, 3)
    assert container.b == [4, 5, 6]
    assert container.c == ('7', '9', '11')
    assert container.d == [10, 11, 12]

# print(Container.get_help_text())
