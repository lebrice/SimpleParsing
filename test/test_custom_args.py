import argparse

from dataclasses import dataclass

from test.testutils import TestSetup, raises

from simple_parsing import ArgumentParser
from simple_parsing.utils import field
from typing import Any


def test_custom_args():
    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(default="/out", aliases=["-o", "--out"], choices=["/out", "/bob"])
    
    foo = Foo.setup("--output_dir /bob")
    assert foo.output_dir == "/bob"

    with raises(argparse.ArgumentError):
        foo = Foo.setup("-o /cat")
        assert foo.output_dir == "/cat"

    foo = Foo.setup("--out /bob")
    assert foo.output_dir == "/bob"


def test_custom_action_args():
    value = 0
    class CustomAction(argparse.Action):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
        
        def __call__(self, parser, namespace, values, dest):
            nonlocal value
            value += 1

    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(type=str, nargs="?", action=CustomAction)
    
    foo = Foo.setup("--output_dir")
    assert foo.output_dir == None
    assert value == 1


def test_custom_nargs():
    """Shows that you can use 'nargs' with the field() function. """
    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(type=str, nargs=2)
    
    with raises(argparse.ArgumentError):    
        foo = Foo.setup("--output_dir")
    
    with raises(argparse.ArgumentError):    
        foo = Foo.setup("--output_dir hey")
    
    foo = Foo.setup("--output_dir john bob")
    assert foo.output_dir == ["john", "bob"]



def test_custom_store_actions():
    """Shows that you can use 'nargs' with the field() function. """
    @dataclass
    class Foo(TestSetup):
        debug: bool = field(aliases=["-d", "-debug"],  action="store_true")
        verbose: bool = field(aliases=["-v", "-verb"], action="store_true")
        no_pruning: bool = field(action="store_false")
    
    foo: Foo = Foo.setup("--verbose --no_pruning")
    assert foo.debug == False
    assert foo.verbose == True
    assert foo.no_pruning == False
    