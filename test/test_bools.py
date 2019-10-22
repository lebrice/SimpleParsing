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
class Base(ParseableFromCommandLine, TestSetup):
    """ Some extension of base-class `Base` """
    a: int = 5
    f: bool = False


@dataclass()
class Flags(ParseableFromCommandLine, TestSetup):
    a: bool # an example required flag (defaults to False)
    b: bool = True # optional flag 'b'.
    c: bool = False # optional flag 'c'.

def test_bool_attributes_work():
    args = Base.setup("--a 5 --f")
    ext = Base.from_args(args)
    assert ext.f == True

    args = Base.setup("--a 5")
    ext = Base.from_args(args)
    assert ext.f == False

    true_strings = ["True", "true"]
    for s in true_strings:
        args = Base.setup(f"--a 5 --f {s}")
        ext = Base.from_args(args)
        assert ext.f == True

    false_strings = ["False", "false"]
    for s in false_strings:
        args = Base.setup(f"--a 5 --f {s}")
        ext = Base.from_args(args)
        assert ext.f == False


def test_bool_flags_work():
    args = Flags.setup("--a true --b --c")
    flags = Flags.from_args(args)
    assert flags.a == True
    assert flags.b == False
    assert flags.c == True