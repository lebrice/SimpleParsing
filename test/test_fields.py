from dataclasses import dataclass

from simple_parsing import ArgumentParser, ConflictResolution, field


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


from enum import Enum
from typing import Dict, List, Optional, Tuple, Type

import pytest


class Color(Enum):
    blue: str = "BLUE"
    red: str = "RED"
    green: str = "GREEN"
    orange: str = "ORANGE"


from simple_parsing.utils import str2bool
from simple_parsing.wrappers.field_parsing import parse_enum


@pytest.mark.xfail(
    reason="Removed this function. TODO: see https://github.com/lebrice/SimpleParsing/issues/150."
)
@pytest.mark.parametrize(
    "annotation, expected_options",
    [
        (Tuple[int, int], dict(nargs=2, type=int)),
        (Tuple[Color, Color], dict(nargs=2, type=parse_enum(Color))),
        (
            Optional[Tuple[Color, Color]],
            dict(nargs=2, type=parse_enum(Color), required=False),
        ),
        (List[str], dict(nargs="*", type=str)),
        (Optional[List[str]], dict(nargs="*", type=str, required=False)),
        (Optional[str], dict(nargs="?", type=str, required=False)),
        (Optional[bool], dict(nargs="?", type=str2bool, required=False)),
        # (Optional[Tuple[Color, str]], dict(nargs=2, type=get_parsing_fn(Tuple[Color, str]), required=False)),
    ],
)
def test_generated_options_from_annotation(annotation: Type, expected_options: Dict):
    raise NotImplementedError(
        """
        TODO: Would be a good idea to refactor the FieldWrapper class a bit. The args_dict (a dict
        of all the argparse arguments for a given field, that get passed to parser.add_arguments
        in the FieldWrapper) is currently created using a mix of three things (with increasing
        priority):
        - The type annotation
        - The dataclass context (e.g. when adding an Optional[Dataclass] field on another
          dataclass, or when using the `default` or `prefix` arguments to `parser.add_arguments`.
        - The manual overrides (arguments of `parser.add_argument` passed to the `field` function)

        These three are currently a bit mixed together in the `FieldWrapper` class. It would be
        preferable to design a way for them to be cleanly separated.
        """
    )
    # from simple_parsing.wrappers.field_wrapper import get_argparse_options_for_annotation

    # actual_options = get_argparse_options_for_annotation(annotation)
    # for option, expected_value in expected_options.items():
    #     assert actual_options[option] == expected_value
