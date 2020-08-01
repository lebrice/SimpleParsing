import argparse
import textwrap
from dataclasses import dataclass, fields

from .testutils import *


def test_tuple_any_becomes_string():
    @dataclass
    class Container(TestSetup):
        strings: Tuple = (64, 128, 256, 512)

    c = Container.setup("")
    assert c.strings == (64, 128, 256, 512)
    c = Container.setup("--strings 12 24 36")
    assert c.strings == ("12", "24", "36")


def test_tuple_with_n_items_takes_only_n_values():
    @dataclass
    class Container(TestSetup):
        ints: Tuple[int, int] = (1, 5)

    c = Container.setup("")
    assert c.ints == (1, 5)
    with raises_unrecognized_args("6", "7", "8"):
        c = Container.setup("--ints 4 5 6 7 8")


def test_tuple_elipsis_takes_any_number_of_args():
    @dataclass
    class Container(TestSetup):
        ints: Tuple[int, ...] = (1, 2, 3)
    c = Container.setup("")
    assert c.ints == (1, 2, 3)
    c = Container.setup("--ints 4 5 6 7 8")
    assert c.ints == (4, 5, 6, 7, 8)

def test_tuple_with_ellipsis_help_format():
    @dataclass
    class Container(TestSetup):
        ints: Tuple[int, ...] = (1, 2, 3)

    assert_help_output_equals(Container.get_help_text(), f"""
        usage: pytest [-h] [--ints int [int, ...]]
        
        optional arguments:
          -h, --help            show this help message and exit
        
        test_tuple_with_ellipsis_help_format.<locals>.Container ['container']:
          Container(ints: Tuple[int, ...] = (1, 2, 3))
        
          --ints int [int, ...], --container.ints int [int, ...]
        """)

def test_each_type_is_used_correctly():
    
    @dataclass
    class Container(TestSetup):
        """ A container with mixed items in a tuple. """
        mixed: Tuple[int, str, bool, float] = (1, "bob", False, 1.23)
    
    c = Container.setup("")
    assert c.mixed == (1, "bob", False, 1.23)
    
    c = Container.setup("--mixed 1 2 0 1")
    assert c.mixed == (1, "2", False, 1.0)
    
    assert_help_output_equals(Container.get_help_text(), """
    usage: pytest [-h] [--mixed int str bool float]

    optional arguments:
    -h, --help            show this help message and exit

    test_each_type_is_used_correctly.<locals>.Container ['container']:
    A container with mixed items in a tuple. 

      --mixed int str bool float, --container.mixed int str bool float
    """)


def test_issue_29():
    from simple_parsing import ArgumentParser
    @dataclass
    class MyCli:
        asdf: Tuple[str, ...]

    parser = ArgumentParser()
    parser.add_arguments(MyCli, dest="args")
    args = parser.parse_args("--asdf asdf fgfh".split())
    assert args.args == MyCli(asdf=("asdf", "fgfh"))
