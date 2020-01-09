"""Tests for weird conflicts.
"""
from dataclasses import dataclass
from simple_parsing import ArgumentParser

from .testutils import *

def test_arg_and_dataclass_with_same_name(silent):
    @dataclass
    class SomeClass:
        a: int = 1 # some docstring for attribute 'a'

    parser = ArgumentParser()
    parser.add_argument("--a", default=123)
    with raises(argparse.ArgumentError):   
        parser.add_arguments(SomeClass, dest="some_class")
        args = parser.parse_args("")

    
def test_arg_and_dataclass_with_same_name_after_prefixing(silent):
    @dataclass
    class SomeClass:
        a: int = 1 # some docstring for attribute 'a'

    @dataclass
    class Parent:
        pre: SomeClass = SomeClass()
        bla: SomeClass = SomeClass()

    parser = ArgumentParser()
    parser.add_argument("--pre.a", default=123, type=int)
    with raises(argparse.ArgumentError):
        parser.add_arguments(Parent, dest="some_class")
        args = parser.parse_args("--pre.a 123 --pre.a 456".split())