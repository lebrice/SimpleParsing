from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import TypeVar

import pytest

from simple_parsing import ArgumentParser, subgroups

from .testutils import TestSetup, raises_missing_required_arg


@dataclass
class A:
    a: float = 0.0


@dataclass
class B:
    b: str = "bar"


@dataclass
class AB(TestSetup):
    a_or_b: A | B = subgroups({"a": A, "b": B}, default_factory=A)


TestClass = TypeVar("TestClass", bound=TestSetup)


class TestSimpleSubgroup:
    def test_help_action(self):
        """Test that the arguments for the chosen subgroup are shown in the help string."""
        assert "--a_or_b" in AB.get_help_text("--help")
        assert False, AB.get_help_text("--help")

        assert "--a float" in AB.get_help_text("--a_or_b a --help")
        assert "--ab_or_cd.c" in AB.get_help_text("--ab_or_cd cd --help")

        # The default for ab_or_cd is of type CD, so if the option isn't passed, it should show the
        # help for the default subgroup choice.
        assert "--ab_or_cd.c" in AB.get_help_text("--help")

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
        ],
    )
    def test_subgroup(self, dataclass_type: type[TestClass], args: str, expected: TestClass):
        assert dataclass_type.setup(args) == expected


# @dataclass
# class C:
#     c: bool = False


# @dataclass
# class D:
#     d: int = 0


# @dataclass
# class CD:
#     c_or_d: C | D = subgroups({"c": C, "d": D}, default_factory=C)

#     other_c_arg: str = "bob"


# @dataclass
# class ABCD:
#     ab_or_cd: AB | CD = subgroups({"ab": AB, "cd": CD}, default_factory=AB)


# @dataclass
# class E:
#     e: bool = False


# @dataclass
# class F:
#     f: str = "f_default"


# @dataclass
# class EF:
#     e_or_f: E | F = subgroups({"e": E, "f": F}, default_factory=E)


# @dataclass
# class MultipleSubgroupsDifferentNestingLevel(TestSetup):
#     ab_or_cd: Union[AB, CD] = subgroups({"ab": AB, "cd": CD}, default_factory=CD)
#     ef: EF = field(default_factory=EF)


# @dataclass
# class NestedSubgroups(TestSetup):
#     ab_or_cd: AB | CD = subgroups(
#         {"ab": AB, "cd": CD},
#         default_factory=AB,
#     )


def test_remove_help_action():
    # Test that it's possible to remove the '--help' action from a parser that had add_help=True

    parser = ArgumentParser(add_help=True)
    parser.add_arguments(A, "a")
    parser.add_arguments(B, "b")
    parser._remove_help_action()

    args, unused = parser.parse_known_args(shlex.split("--a 123 --b foo --help"))
    assert unused == ["--help"]
    assert args.a == A(a=123)
    assert args.b == B(b="foo")


def test_required_subgroup():
    """Test when a subgroup doesn't have a default value, and is required."""

    @dataclass
    class RequiredSubgroup(TestSetup):
        a_or_b: A | B = subgroups({"a": A, "b": B})

    with raises_missing_required_arg():
        assert RequiredSubgroup.setup("")

    assert RequiredSubgroup.setup("--a_or_b b") == RequiredSubgroup(a_or_b=B())


# @dataclass
# class WithRequiredArg:
#     some_required_arg: int
#     other_arg: int = 123


# def test_subgroup_with_required_argument():
#     """Test where a subgroup has a required argument."""

#     @dataclass
#     class Bob(TestSetup):
#         thing: Union[AB, WithRequiredArg] = subgroups({"foo": AB, "req": WithRequiredArg})

#     assert Bob.setup("--thing foo --thing.a 44") == Bob(thing=AB(a=44))
#     assert Bob.setup("--thing req --thing.some_required_arg 22") == Bob(
#         thing=WithRequiredArg(some_required_arg=22)
#     )
#     with raises_missing_required_arg():
#         assert Bob.setup("--thing req")


# def test_two_subgroups():
#     @dataclass
#     class Bob(TestSetup):
#         first: Union[AB, CD] = subgroups({"foo": AB, "bar": CD}, default=CD(d=3))
#         second: Union[EF, GH] = subgroups({"baz": EF, "blop": GH}, default=GH())

#     bob = Bob.setup("--first foo --first.a 123 --second blop --second.g arwg --second.h 1.2")
#     assert bob == Bob(first=AB(a=123), second=GH(g="arwg", h=1.2))


# def test_two_subgroups_with_conflict():
#     @dataclass
#     class Bob(TestSetup):
#         first: Union[AB, CD] = subgroups({"foo": AB, "bar": CD}, default=CD(d=3))
#         second: Union[AB, GH] = subgroups({"foo": AB, "blop": GH}, default=GH())

#     assert Bob.setup(
#         "--first foo --first.a 123 --second blop --second.g arwg --second.h 1.2"
#     ) == Bob(first=AB(a=123), second=GH(g="arwg", h=1.2))

#     assert Bob.setup("--first foo --first.a 123 --second foo --second.a 456") == Bob(
#         first=AB(a=123), second=AB(a=456)
#     )


# def test_unrelated_arg_raises_error():
#     @dataclass
#     class Bob(TestSetup):
#         first: Union[AB, CD] = subgroups({"foo": AB, "bar": CD}, default=CD(d=3))
#         second: Union[AB, GH] = subgroups({"foo": AB, "blop": GH}, default=GH())

#     with raises_unrecognized_args("--bblarga"):
#         Bob.setup("--first foo --first.a 123 --second foo --second.a 456 --bblarga")


# @dataclass
# class Person:
#     age: int


# @dataclass
# class Daniel(Person):
#     """Person named Bob."""

#     age: int = 32
#     cool: bool = True


# @dataclass
# class Alice(Person):
#     """Person named Alice."""

#     age: int = 13
#     popular: bool = True


# @dataclass
# class NestedSubgroups(TestSetup):
#     """Configuration dataclass."""

#     person: Person = subgroups({"daniel": Daniel, "alice": Alice}, default=Daniel)


# @dataclass
# class HigherConfig(TestSetup):
#     """Higher-level config."""

#     a: NestedSubgroups = NestedSubgroups(person=Daniel())
#     b: NestedSubgroups = NestedSubgroups(person=Alice())


# def test_mixing_subgroup_with_regular_dataclass():

#     parser = ArgumentParser()
#     parser.add_arguments(NestedSubgroups, dest="config")
#     parser.add_arguments(AB, dest="foo")

#     args = parser.parse_args([])
#     assert args.config == NestedSubgroups(person=Daniel())
#     assert args.foo == AB()

#     # NOTE: Not sure if the parser can safely be reused twice.
#     parser = ArgumentParser()
#     parser.add_arguments(NestedSubgroups, dest="config")
#     parser.add_arguments(AB, dest="foo")
#     args = parser.parse_args(shlex.split("--person alice --person.age=33 --a 123"))
#     assert args.config == NestedSubgroups(person=Alice(age=33))
#     assert args.foo == AB(a=123)


# def test_issue_139():
#     """test for https://github.com/lebrice/SimpleParsing/issues/139

#     Need to save the chosen subgroup name somewhere on the args.
#     """

#     parser = ArgumentParser()
#     parser.add_arguments(NestedSubgroups, dest="config")

#     args = parser.parse_args([])
#     assert args.config == NestedSubgroups(person=Daniel())
#     assert args.subgroups == {"config.person": "daniel"}


# def test_deeper_nesting_prefixing():
#     """Test that the prefixing mechanism works for deeper nesting of subgroups."""

#     assert "--a.person.cool" in HigherConfig.get_help_text(
#         "--help",
#         nested_mode=NestedMode.WITHOUT_ROOT,
#         argument_generation_mode=ArgumentGenerationMode.NESTED,
#     )

#     assert "--a.person.popular" in HigherConfig.get_help_text(
#         "--a.person alice --help",
#         nested_mode=NestedMode.WITHOUT_ROOT,
#         argument_generation_mode=ArgumentGenerationMode.NESTED,
#     )

#     assert HigherConfig.setup("") == HigherConfig()
#     assert HigherConfig.setup("--a.person alice") == HigherConfig(a=NestedSubgroups(person=Alice()))
#     assert HigherConfig.setup("--b.person daniel --b.person.age 54") == HigherConfig(
#         b=NestedSubgroups(person=Daniel(age=54))
#     )


# def test_subgroups_dict_in_args():
#     parser = ArgumentParser()
#     parser.add_arguments(HigherConfig, "config")

#     args = parser.parse_args([])
#     assert args.config == HigherConfig()
#     assert args.subgroups == {"config.a.person": "daniel", "config.b.person": "alice"}

#     args = parser.parse_args(shlex.split("--a.person alice --b.person daniel --b.person.age 54"))
#     assert args.subgroups == {"config.a.person": "alice", "config.b.person": "daniel"}
