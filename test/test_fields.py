from dataclasses import dataclass
from enum import Enum
from typing import Optional

import pytest

import simple_parsing
from simple_parsing import ArgumentParser, ConflictResolution, field
from simple_parsing.utils import str2bool
from simple_parsing.wrappers.field_parsing import parse_enum


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


@pytest.mark.parametrize("args, expected_a", [("", 1), ("--a 5", 5)])
def test_cmd_false_field_uses_parent_default(args: str, expected_a: int):
    """cmd=False fields of a nested dataclass keep the value of the parent's default (#371)."""

    @dataclass
    class Inner:
        a: int = 0
        b: list[int] = field(default_factory=list, cmd=False)

    @dataclass
    class Outer:
        inner: Inner = field(default_factory=lambda: Inner(a=1, b=[1, 2, 3]))

    assert simple_parsing.parse(Outer, args=args) == Outer(Inner(a=expected_a, b=[1, 2, 3]))


def test_cmd_false_field_uses_default_passed_to_parser():
    @dataclass
    class A:
        a: int = 0
        b: list[int] = field(default_factory=list, cmd=False)

    default = A(a=1, b=[1, 2, 3])
    result = simple_parsing.parse(A, args="--a 2", default=default)
    assert result == A(a=2, b=[1, 2, 3])
    # The parsed value is a copy, not the default's own list.
    assert result.b is not default.b


class Color(Enum):
    blue: str = "BLUE"
    red: str = "RED"
    green: str = "GREEN"
    orange: str = "ORANGE"


@pytest.mark.xfail(
    reason="Removed this function. TODO: see https://github.com/lebrice/SimpleParsing/issues/150."
)
@pytest.mark.parametrize(
    "annotation, expected_options",
    [
        (tuple[int, int], dict(nargs=2, type=int)),
        (tuple[Color, Color], dict(nargs=2, type=parse_enum(Color))),
        (
            Optional[tuple[Color, Color]],
            dict(nargs=2, type=parse_enum(Color), required=False),
        ),
        (list[str], dict(nargs="*", type=str)),
        (Optional[list[str]], dict(nargs="*", type=str, required=False)),
        (Optional[str], dict(nargs="?", type=str, required=False)),
        (Optional[bool], dict(nargs="?", type=str2bool, required=False)),
        # (Optional[Tuple[Color, str]], dict(nargs=2, type=get_parsing_fn(Tuple[Color, str]), required=False)),
    ],
)
def test_generated_options_from_annotation(annotation: type, expected_options: dict):
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
