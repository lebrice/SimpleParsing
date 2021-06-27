

from dataclasses import dataclass

from test.testutils import TestSetup

from simple_parsing import ArgumentParser, field, ConflictResolution


def test_cmd_false_doesnt_create_conflicts():
    @dataclass
    class A:
        batch_size: int = field(default=10, cmd=False)
        
    @dataclass
    class B:
        batch_size: int = 20
    
    # @dataclass
    # class Foo(TestSetup):
    #     a: A = mutable_field(A)
    #     b: B = mutable_field(B)
    
    parser = ArgumentParser(conflict_resolution=ConflictResolution.NONE)
    parser.add_arguments(A, "a")
    parser.add_arguments(B, "b")
    args = parser.parse_args("--batch_size 32".split())
    a: A = args.a
    b: B = args.b
    assert a == A()
    assert b == B(batch_size=32)
 
from typing import Type, Dict, Tuple, List, Optional
from simple_parsing.wrappers.field_wrapper import get_argparse_options_for_annotation
import pytest

from enum import Enum


class Color(Enum):
    blue: str = "BLUE"
    red: str = "RED"
    green: str = "GREEN"
    orange: str = "ORANGE"


from simple_parsing.wrappers.field_parsing import get_parsing_fn

from simple_parsing.utils import str2bool


@pytest.mark.parametrize("annotation, expected_options", [
    (Tuple[int, int], dict(nargs=2, type=int)),
    (Tuple[Color, Color], dict(nargs=2, type=Color)),
    (Optional[Tuple[Color, Color]], dict(nargs=2, type=Color, required=False)),
    (List[str], dict(nargs="*", type=str)),
    (Optional[List[str]], dict(nargs="*", type=str, required=False)),
    (Optional[str], dict(nargs="?", type=str, required=False)),
    (Optional[bool], dict(nargs="?", type=str2bool, required=False)),
    # (Optional[Tuple[Color, str]], dict(nargs=2, type=get_parsing_fn(Tuple[Color, str]), required=False)),
])
def test_generated_options_from_annotation(annotation: Type, expected_options: Dict):
    actual_options = get_argparse_options_for_annotation(annotation)
    for option, expected_value in expected_options.items():
        assert actual_options[option] == expected_value
