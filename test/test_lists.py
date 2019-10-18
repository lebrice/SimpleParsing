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
from testutils import Setup

@dataclass()
class Container(ParseableFromCommandLine, Setup):
    a: Tuple[int]
    b: List[int]
    c: Tuple[str] = field(default_factory=tuple)
    d: List[int] = field(default_factory=list)

def test_list_attributes_work():
    args = Container.setup("--a 1 2 3 --b 4 5 6 --c 7 8 9 --d 10 11 12")
    container = Container.from_args(args)
    assert container.a == (1, 2, 3)
    assert container.b == [4, 5, 6]
    assert container.c == ('7', '8', '9')
    assert container.d == [10, 11, 12]

    # required attributes still work.
    with contextlib.suppress(SystemExit), pytest.raises(argparse.ArgumentError):
        args = Container.setup("--b 4")

    args = Container.setup("--a 1 2 --b 2 --c 3 4 5 --d 10 11 12")
    container = Container.from_args(args)
    assert container.a == (1,2)
    assert container.b == [2]
    assert container.c == ('3', '4', '5')
    assert container.d == [10, 11, 12]

def test_list_multiple_work():
    args = Container.setup('--a "1 2 3" "4 5 6" --b "4 5 6" "7 8 9" --c "7 8 9" "7 9 11" --d 10 11 12', multiple=True)
    containers = Container.from_args_multiple(args)
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
