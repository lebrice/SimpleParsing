import argparse
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
    with raises_expected_n_args(2):
        c = Container.setup("--ints 4 5 6 7 8")
        assert False    


def test_tuple_elipsis_takes_any_number_of_args():
    @dataclass
    class Container(TestSetup):
        ints: Tuple[int, ...] = (1, 2, 3)
    c = Container.setup("")
    assert c.ints == (1, 2, 3)
    c = Container.setup("--ints 4 5 6 7 8")
    assert c.ints == (4, 5, 6, 7, 8)


def test_each_type_is_used_correctly():
    
    @dataclass
    class Container(TestSetup):
        mixed: Tuple[int, str, bool, float] = (1, "bob", False, 1.23)
    c = Container.setup("")
    assert c.mixed == (1, "bob", False, 1.23)
    c = Container.setup("--mixed 1 2 0 1")
    assert c.mixed == (1, "2", False, 1.0)
