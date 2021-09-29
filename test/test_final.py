from dataclasses import dataclass

from .testutils import *

try:
    from typing import Final
except:
    from typing_extensions import Final


def test_final_argument(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: Final[some_type] = expected_value

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest="some_class")

    args = parser.parse_args("")
    assert args == argparse.Namespace(some_class=SomeClass(a=expected_value))
