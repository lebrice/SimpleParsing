import argparse

from dataclasses import dataclass

from test.testutils import TestSetup, raises

from simple_parsing import ArgumentParser
from simple_parsing.utils import field

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
        
        def __call__(self, *args, **kwargs):
            nonlocal value
            value += 1
            print("HELLO HELLO", args, kwargs)

    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(default="bob", action=CustomAction)
    
    foo = Foo.setup("--output_dir doesnt_matter")
    assert foo.output_dir == "bob"
    assert value == 1

