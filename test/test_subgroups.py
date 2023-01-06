from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import TypeVar

import pytest

from simple_parsing import ArgumentParser, subgroups

from .test_choice import Color
from .testutils import TestSetup, raises_missing_required_arg

TestClass = TypeVar("TestClass", bound=TestSetup)


@dataclass
class A:
    a: float = 0.0


@dataclass
class B:
    b: str = "bar"


@dataclass
class AB(TestSetup):
    a_or_b: A | B = subgroups({"a": A, "b": B}, default_factory=A)


@dataclass
class C:
    c: bool = False


@dataclass
class D:
    d: int = 0


@dataclass
class E:
    e: bool = False


@dataclass
class F:
    f: str = "f_default"


@dataclass
class G:
    g: int = 0


@dataclass
class H:
    h: bool = False


@dataclass
class CD:
    c_or_d: C | D = subgroups({"c": C, "d": D}, default_factory=C)
    other_c_arg: str = "bob"


@dataclass
class EF:
    e_or_f: E | F = subgroups({"e": E, "f": F}, default_factory=E)


@dataclass
class GH:
    g_or_h: G | H = subgroups({"g": G, "h": H}, default_factory=G)


@dataclass
class ABCD(TestSetup):
    ab_or_cd: AB | CD = subgroups({"ab": AB, "cd": CD}, default_factory=AB)


@dataclass
class EFGH:
    ef_or_gh: EF | GH = subgroups({"ef": EF, "gh": GH}, default_factory=EF)


@dataclass
class ABCDEFGH(TestSetup):
    """Dataclass with three levels of subgroup nesting."""

    abc_or_efgh: ABCD | EFGH = subgroups({"abcd": ABCD, "efgh": EFGH}, default_factory=ABCD)


@dataclass
class MultipleSubgroupsSameLevel(TestSetup):
    a_or_b: A | B = subgroups({"a": A, "b": B}, default_factory=A)
    c_or_d: C | D = subgroups({"c": C, "d": D}, default_factory=D)


@dataclass
class MultipleSubgroupsDifferentLevel(TestSetup):
    ab_or_cd: AB | CD = subgroups({"ab": AB, "cd": CD}, default_factory=CD)
    ef: EF = field(default_factory=EF)


@dataclass
class EnumsAsKeys(TestSetup):
    """Dataclass where the subgroup choices are keys."""

    a_or_b: A | B = subgroups({Color.red: A, Color.blue: B}, default_factory=A)


@pytest.mark.parametrize(
    "dataclass_type, get_help_text_args, should_contain",
    [
        (AB, {}, ["--a_or_b {a,b}", "--a float"]),
        (AB, {}, ["--a_or_b {a,b}       (default: a)", "--a float"]),
        (EnumsAsKeys, {}, ["--a_or_b {Color.red,Color.blue}", "--a float"]),
        (
            MultipleSubgroupsSameLevel,
            {},
            ["--a_or_b {a,b}", "--a float", "--c_or_d {c,d}", "--d int"],
        ),
        (
            MultipleSubgroupsDifferentLevel,
            {},
            ["--ab_or_cd {ab,cd}", "--c_or_d {c,d}", "--e_or_f {e,f}", "--e bool"],
        ),
    ],
)
def test_help_string(
    dataclass_type: type[TestClass],
    get_help_text_args: dict,
    should_contain: list[str],
):
    """Test that the arguments for the chosen subgroup are shown in the help string."""
    help_text = dataclass_type.get_help_text(*get_help_text_args)
    for expected in should_contain:
        assert expected in help_text


@pytest.mark.parametrize(
    "dataclass_type, args, expected",
    [
        (
            AB,
            "--a_or_b a --a 123",
            AB(a_or_b=A(a=123)),
        ),
        (
            AB,
            "--a_or_b b --b foooo",
            AB(a_or_b=B(b="foooo")),
        ),
        (
            MultipleSubgroupsSameLevel,
            "--a_or_b a --a 123 --d 456",
            MultipleSubgroupsSameLevel(a_or_b=A(a=123), c_or_d=D(d=456)),
        ),
        (
            MultipleSubgroupsSameLevel,
            "--a_or_b b --b foooo",
            MultipleSubgroupsSameLevel(a_or_b=B(b="foooo")),
        ),
        (
            ABCD,
            "--ab_or_cd ab --a_or_b a --a 123",
            ABCD(ab_or_cd=AB(a_or_b=A(a=123))),
        ),
        (
            ABCD,
            "--ab_or_cd cd --c_or_d d --d 456",
            ABCD(ab_or_cd=CD(c_or_d=D(d=456))),
        ),
    ],
)
def test_parse(dataclass_type: type[TestClass], args: str, expected: TestClass):
    assert dataclass_type.setup(args) == expected


def test_subgroup_choice_is_saved_on_namespace():
    """test for https://github.com/lebrice/SimpleParsing/issues/139

    Need to save the chosen subgroup name somewhere on the args.
    """
    parser = ArgumentParser()
    parser.add_arguments(AB, dest="config")

    args = parser.parse_args(shlex.split("--a_or_b b --b foobar"))
    assert args.config == AB(a_or_b=B(b="foobar"))
    assert args.subgroups == {"config.a_or_b": "b"}


@dataclass
class RequiredSubgroup(TestSetup):
    a_or_b: A | B = subgroups({"a": A, "b": B})


def test_required_subgroup():
    """Test when a subgroup doesn't have a default value, and is required."""

    with raises_missing_required_arg():
        assert RequiredSubgroup.setup("")

    assert RequiredSubgroup.setup("--a_or_b b") == RequiredSubgroup(a_or_b=B())


@dataclass
class TwoSubgroupsWithConflict(TestSetup):
    first: AB | CD = subgroups({"ab": AB, "cd": CD}, default_factory=CD)
    second: AB | GH = subgroups({"ab": AB, "gh": GH}, default_factory=GH)


@pytest.mark.parametrize(
    "args_str, expected",
    [
        (
            (
                "--first ab --first.a_or_b a --first.a_or_b.a 111 "
                "--second ab --second.a_or_b a --second.a_or_b.a 234"
            ),
            TwoSubgroupsWithConflict(first=AB(a_or_b=A(a=111)), second=AB(a_or_b=A(a=234))),
        ),
        (
            # TODO: Unsure about this one. Also have to be careful about the abbrev feature of
            # Argparse.
            "--first ab --first.a_or_b a --a 111 --second ab --second.a_or_b b --b arwg",
            TwoSubgroupsWithConflict(first=AB(a_or_b=A(a=111)), second=AB(a_or_b=B(b="arwg"))),
        ),
    ],
)
def test_two_subgroups_with_conflict(args_str: str, expected: TwoSubgroupsWithConflict):
    assert TwoSubgroupsWithConflict.setup(args_str) == expected


def test_typing_of_subgroups_function():

    with pytest.raises(ValueError):
        _ = subgroups({"a": A, "b": lambda: B()})

    # TODO: There should be a typing errors here. How do I check for it programmatically?
    from typing_extensions import reveal_type

    # note: This should raise an error, ideally, since B isn't in the dict values.
    # Either that, or it should have a type of `A | B`.
    bob = subgroups({"a": A, "aa": A}, default_factory=B)
    reveal_type(bob)
