import contextlib
import shlex
from dataclasses import dataclass, is_dataclass
from io import StringIO
from typing import Union

import pytest

from simple_parsing import ArgumentParser, subgroups
from simple_parsing.wrappers.field_wrapper import ArgumentGenerationMode, NestedMode

from .testutils import TestSetup, raises_missing_required_arg, raises_unrecognized_args


@dataclass
class Foo:
    a: int = 1
    b: int = 2


@dataclass
class Bar:
    c: int = 1
    d: int = 2


@dataclass
class Baz:
    e: int = 1
    f: bool = False


@dataclass
class Blop:
    g: str = "arwg"
    h: float = 1.2


@dataclass
class Bob(TestSetup):
    thing: Union[Foo, Bar] = subgroups({"foo_thing": Foo, "bar_thing": Bar}, default=Bar(d=3))


def test_remove_help_action():
    # Test that it's possible to remove the '--help' action from a parser that had add_help=True

    parser = ArgumentParser(add_help=True)
    parser.add_arguments(Foo, "foo")
    parser.add_arguments(Bar, "bar")
    parser._remove_help_action()
    import shlex

    args, unused = parser.parse_known_args(shlex.split("--a 123 --c 456 --help"))
    assert unused == ["--help"]
    assert args.foo == Foo(a=123)
    assert args.bar == Bar(c=456)


class TestSubgroup:
    def test_subgroup(self):
        parser = ArgumentParser()
        parser.add_arguments(Bob, dest="bob")
        args = parser.parse_args(shlex.split("--thing foo_thing --thing.a 123"))
        bob = args.bob
        thing = bob.thing
        assert is_dataclass(thing)
        assert thing == Foo(a=123)

    def test_help_action(self):
        """Test that the arguments for the chosen subgroup are shown in the help string."""

        # The default is of type Bar, so if the option isn't passed, it should show the help for
        # the default argument choice.
        assert "--thing.c" in Bob.get_help_text("--help")

        assert "--thing.a" in Bob.get_help_text("--thing foo_thing --help")
        assert "--thing.c" in Bob.get_help_text("--thing bar_thing --help")

    def test_manual_help_action(self):
        """Test without the use of `get_help_text` from TestSetup, just to be sure."""
        parser = ArgumentParser()
        parser.add_arguments(Bob, dest="bob")

        with StringIO() as f:
            with contextlib.suppress(SystemExit), contextlib.redirect_stdout(f):
                parser.parse_args(["--help"])
            help_text = f.getvalue()
        # print("\n" + help_text)
        assert "--thing.c" in help_text

    @pytest.mark.xfail(reason="TODO, doesn't quite work yet.")
    def test_print_help(self):
        parser = ArgumentParser()
        parser.add_arguments(Bob, dest="bob")

        with StringIO() as f:
            parser.print_help(f)
            help_text = f.getvalue()
            print(help_text)
            assert "--thing.c" in help_text


def test_required_subgroup():
    """Test when a subgroup doesn't have a default value, and is required."""

    @dataclass
    class Bob(TestSetup):
        thing: Union[Foo, Bar] = subgroups({"foo": Foo, "bar": Bar})

    with raises_missing_required_arg():
        assert Bob.setup("")

    assert Bob.setup("--thing foo") == Bob(thing=Foo())


@dataclass
class WithRequiredArg:
    some_required_arg: int
    other_arg: int = 123


def test_subgroup_with_required_argument():
    """Test where a subgroup has a required argument."""

    @dataclass
    class Bob(TestSetup):
        thing: Union[Foo, WithRequiredArg] = subgroups({"foo": Foo, "req": WithRequiredArg})

    assert Bob.setup("--thing foo --thing.a 44") == Bob(thing=Foo(a=44))
    assert Bob.setup("--thing req --thing.some_required_arg 22") == Bob(
        thing=WithRequiredArg(some_required_arg=22)
    )
    with raises_missing_required_arg():
        assert Bob.setup("--thing req")


def test_two_subgroups():
    @dataclass
    class Bob(TestSetup):
        first: Union[Foo, Bar] = subgroups({"foo": Foo, "bar": Bar}, default=Bar(d=3))
        second: Union[Baz, Blop] = subgroups({"baz": Baz, "blop": Blop}, default=Blop())

    bob = Bob.setup("--first foo --first.a 123 --second blop --second.g arwg --second.h 1.2")
    assert bob == Bob(first=Foo(a=123), second=Blop(g="arwg", h=1.2))


def test_two_subgroups_with_conflict():
    @dataclass
    class Bob(TestSetup):
        first: Union[Foo, Bar] = subgroups({"foo": Foo, "bar": Bar}, default=Bar(d=3))
        second: Union[Foo, Blop] = subgroups({"foo": Foo, "blop": Blop}, default=Blop())

    assert Bob.setup(
        "--first foo --first.a 123 --second blop --second.g arwg --second.h 1.2"
    ) == Bob(first=Foo(a=123), second=Blop(g="arwg", h=1.2))

    assert Bob.setup("--first foo --first.a 123 --second foo --second.a 456") == Bob(
        first=Foo(a=123), second=Foo(a=456)
    )


def test_unrelated_arg_raises_error():
    @dataclass
    class Bob(TestSetup):
        first: Union[Foo, Bar] = subgroups({"foo": Foo, "bar": Bar}, default=Bar(d=3))
        second: Union[Foo, Blop] = subgroups({"foo": Foo, "blop": Blop}, default=Blop())

    with raises_unrecognized_args("--bblarga"):
        Bob.setup("--first foo --first.a 123 --second foo --second.a 456 --bblarga")


@dataclass
class Person:
    age: int


@dataclass
class Daniel(Person):
    """Person named Bob."""

    age: int = 32
    cool: bool = True


@dataclass
class Alice(Person):
    """Person named Alice."""

    age: int = 13
    popular: bool = True


@dataclass
class Config:
    """Configuration dataclass."""

    person: Person = subgroups({"daniel": Daniel, "alice": Alice}, default=Daniel)

    @dataclass
    class Config:
        """Configuration dataclass."""

        person: Person = subgroups({"daniel": Daniel, "alice": Alice}, default=Daniel)


@dataclass
class HigherConfig(TestSetup):
    """Higher-level config."""

    a: Config = Config(person=Daniel())
    b: Config = Config(person=Alice())


def test_mixing_subgroup_with_regular_dataclass():

    parser = ArgumentParser()
    parser.add_arguments(Config, dest="config")
    parser.add_arguments(Foo, dest="foo")

    args = parser.parse_args([])
    assert args.config == Config(person=Daniel())
    assert args.foo == Foo()

    # NOTE: Not sure if the parser can safely be reused twice.
    parser = ArgumentParser()
    parser.add_arguments(Config, dest="config")
    parser.add_arguments(Foo, dest="foo")
    args = parser.parse_args(shlex.split("--person alice --person.age=33 --a 123"))
    assert args.config == Config(person=Alice(age=33))
    assert args.foo == Foo(a=123)


def test_issue_139():
    """test for https://github.com/lebrice/SimpleParsing/issues/139

    Need to save the chosen subgroup name somewhere on the args.
    """

    parser = ArgumentParser()
    parser.add_arguments(Config, dest="config")

    args = parser.parse_args([])
    assert args.config == Config(person=Daniel())
    assert args.subgroups == {"config.person": "daniel"}


def test_deeper_nesting_prefixing():
    """Test that the prefixing mechanism works for deeper nesting of subgroups."""

    assert "--a.person.cool" in HigherConfig.get_help_text(
        "--help",
        nested_mode=NestedMode.WITHOUT_ROOT,
        argument_generation_mode=ArgumentGenerationMode.NESTED,
    )

    assert "--a.person.popular" in HigherConfig.get_help_text(
        "--a.person alice --help",
        nested_mode=NestedMode.WITHOUT_ROOT,
        argument_generation_mode=ArgumentGenerationMode.NESTED,
    )

    assert HigherConfig.setup("") == HigherConfig()
    assert HigherConfig.setup("--a.person alice") == HigherConfig(a=Config(person=Alice()))
    assert HigherConfig.setup("--b.person daniel --b.person.age 54") == HigherConfig(
        b=Config(person=Daniel(age=54))
    )


def test_subgroups_dict_in_args():
    parser = ArgumentParser()
    parser.add_arguments(HigherConfig, "config")

    args = parser.parse_args([])
    assert args.config == HigherConfig()
    assert args.subgroups == {"config.a.person": "daniel", "config.b.person": "alice"}

    args = parser.parse_args(shlex.split("--a.person alice --b.person daniel --b.person.age 54"))
    assert args.subgroups == {"config.a.person": "alice", "config.b.person": "daniel"}
