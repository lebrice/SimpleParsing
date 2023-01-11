from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from functools import partial
from typing import Callable, TypeVar

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


def test_subgroups_with_key_default() -> None:

    with pytest.raises(ValueError):
        subgroups({"a": A, "b": B}, default_factory="a")

    @dataclass
    class Foo(TestSetup):
        a_or_b: A | B = subgroups({"a": A, "b": B}, default="a")

    assert Foo.setup() == Foo(a_or_b=A())
    assert Foo.setup("--a_or_b a --a 445") == Foo(a_or_b=A(a=445))
    assert Foo.setup("--a_or_b b") == Foo(a_or_b=B())
    assert Foo.setup("--a_or_b b --b zodiak") == Foo(a_or_b=B(b="zodiak"))


# IDEA: Make it possible to use a default factory that is a partial for a function, if that
# function has a return annotation.
# def some_a_factory(a: int = -1) -> A:
#     return A(a=a)


def test_subgroup_default_needs_to_be_key_in_dict():
    with pytest.raises(ValueError, match="default must be a key in the subgroups dict"):
        _ = subgroups({"a": B, "aa": A}, default="b")


def test_subgroup_default_factory_needs_to_be_value_in_dict():
    with pytest.raises(ValueError, match="default_factory must be a value in the subgroups dict"):
        _ = subgroups({"a": B, "aa": A}, default_factory=C)


simple_subgroups_for_now = pytest.mark.xfail(
    strict=True,
    reason=(
        "TODO: Not implemented yet. Subgroups only currently allows having a dict with values"
        " that are dataclasses. Remove this once this works."
    ),
)


@simple_subgroups_for_now
@pytest.mark.parametrize(
    "a_factory, b_factory",
    [
        (partial(A), partial(B)),
        (lambda: A(), lambda: B()),
        (partial(A, a=321), partial(B, b="foobar")),
        (lambda: A(a=123), lambda: B(b="foooo")),
    ],
)
def test_other_default_factories(a_factory: Callable[[], A], b_factory: Callable[[], B]):
    """Test using other kinds of default factories (i.e. functools.partial or lambda expressions)"""

    @dataclass
    class Foo(TestSetup):
        a_or_b: A | B = subgroups({"a": a_factory, "b": b_factory}, default="a")

    assert Foo.setup() == Foo(a_or_b=a_factory())
    assert Foo.setup("--a_or_b a --a 445") == Foo(a_or_b=A(a=445))
    assert Foo.setup("--a_or_b b") == Foo(a_or_b=b_factory())


@simple_subgroups_for_now
@pytest.mark.parametrize(
    "a_factory, b_factory",
    [
        (partial(A), partial(B)),
        (lambda: A(), lambda: B()),
        (partial(A, a=321), partial(B, b="foobar")),
        (lambda: A(a=123), lambda: B(b="foooo")),
    ],
)
def test_help_string_displays_default_factory_arguments(
    a_factory: Callable[[], A], b_factory: Callable[[], B]
):
    """The help string should be basically the same when using a `partial` or a lambda that returns
    a dataclass, as using just the class itself.

    When using `functools.partial` or lambda expressions, we'd ideally also like the help text to
    show the field values from inside the `partial` or lambda, if possible.
    """
    # NOTE: Here we need to return just A() and B() with these default factories, so the defaults
    # for the fields are the same
    @dataclass
    class Foo(TestSetup):
        a_or_b: A | B = subgroups({"a": A, "b": B}, default_factory=a_factory)

    @dataclass
    class FooWithDefaultFactories(TestSetup):
        a_or_b: A | B = subgroups({"a": a_factory, "b": b_factory}, default_factory=a_factory)

    help_with = FooWithDefaultFactories.get_help_text()
    help_without = Foo.get_help_text()
    assert (
        help_with.replace("FooWithDefaultFactories", "Foo").replace(
            "foo_with_default_factories", "foo"
        )
        == help_without
    )


@pytest.mark.xfail(strict=True, reason="Not implemented yet. Remove this once it is.")
def test_all_subgroups_are_in_help_string():
    @dataclass
    class Foo(TestSetup):
        a_or_b: A | B = subgroups({"a": A, "b": B}, default_factory=B)

    help_text = Foo.get_help_text()

    assert "-a float, --a float  (default: 0.0)" in help_text
    assert "-b str, --b str  (default: bar)" in help_text


def test_typing_of_subgroups_function() -> None:
    """TODO: There should be a typing errors here. Could we check for it programmatically?"""
    # note: This should raise an error with the type checker:
    bob: A = subgroups({"a": A, "b": B})  # noqa: F841
    # reveal_type(bob)

    with pytest.raises(ValueError):
        other: A | B = subgroups({"a": A, "b": B}, default_factory=C)  # noqa: F841
    # reveal_type(other)


@dataclass
class ModelConfig:
    ...


@dataclass
class ModelAConfig(ModelConfig):
    lr: float = 3e-4
    optimizer: str = "Adam"
    betas: tuple[float, float] = (0.9, 0.999)


@dataclass
class ModelBConfig(ModelConfig):
    lr: float = 1e-3
    optimizer: str = "SGD"
    momentum: float = 1.234


@dataclass
class Config:

    # Which model to use
    model: ModelConfig = subgroups(
        {"model_a": ModelAConfig, "model_b": ModelBConfig},
        default_factory=ModelAConfig,
    )


def test_destination_substring_of_other_destination_issue191():
    """Test for https://github.com/lebrice/SimpleParsing/issues/191"""

    parser = ArgumentParser()
    parser.add_arguments(Config, dest="config")
    parser.add_arguments(Config, dest="config2")  # this produces and exception
    # parser.add_arguments(Config, dest="something") # this works as expected
    args = parser.parse_args("")

    config: Config = args.config
    assert config.model == ModelAConfig()
