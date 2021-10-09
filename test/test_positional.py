import pytest
from dataclasses import dataclass

from simple_parsing import ArgumentParser, field

from .testutils import *
from typing import List

def test_single_posarg():
    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(positional=True)
        extra_flag: bool = False
    foo = Foo.setup("/bob --extra_flag")
    assert foo.output_dir == "/bob"
    assert foo.extra_flag

def test_repeated_posarg():
    @dataclass
    class Foo(TestSetup):
        output_dir: List[str] = field(positional=True)
        extra_flag: bool = False
    # Here we see why 'invoke' wrote their own parser. Doesn't seem obvious how to explain to argparse that
    # --extra_flag /cherry (which is a little ambiguous) or --extra_flag True /cherry is something we'd like to allow.
    foo = Foo.setup("/alice /bob /cherry --extra_flag")
    assert foo.output_dir == ["/alice", "/bob", "/cherry"]
    assert foo.extra_flag
