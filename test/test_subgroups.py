import contextlib
from dataclasses import dataclass, is_dataclass
from typing import Dict, Optional, Type, TypeVar, Union

from simple_parsing import ArgumentParser, choice

from .testutils import TestSetup, raises_missing_required_arg


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


T = TypeVar("T")


def subgroups(subgroups: Dict[str, Type[T]], *args, default: Optional[T] = None, **kwargs) -> T:
    metadata = kwargs.setdefault("metadata", {})
    metadata["subgroups"] = subgroups
    choices = subgroups.keys()
    kwargs["type"] = str
    # if default not in choices:
    #     raise RuntimeError(f"Default value needs to be one of the choices ({choices})")
    return choice(*choices, *args, default=default, **kwargs)


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
        args = parser.parse_args("--thing foo_thing --thing.a 123".split())
        bob = args.bob
        thing = bob.thing
        assert is_dataclass(thing)
        assert thing == Foo(a=123)

    def test_help_string(self):
        """Test that the arguments for the chosen subgroup are shown in the help string."""
        parser = ArgumentParser()
        parser.add_arguments(Bob, dest="bob")
        from io import StringIO

        with StringIO() as f:
            with contextlib.suppress(SystemExit), contextlib.redirect_stdout(f):
                parser.parse_args(["--help"])
            help_text = f.getvalue()
        print("\n" + help_text)
        assert "--a" in help_text

        with StringIO() as f:
            parser.print_help(f)
            help_text = f.getvalue()
            print(help_text)
            assert "--a" in help_text


def test_required_subgroup():
    """Test when a subgroup doesn't have a default value, and is required."""

    @dataclass
    class Bob(TestSetup):
        thing: Union[Foo, Bar] = subgroups({"foo_thing": Foo, "bar_thing": Bar})

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
    assert Bob.setup("--thing req --some_required_arg 22") == Bob(
        thing=WithRequiredArg(some_required_arg=22)
    )
    with raises_missing_required_arg():
        assert Bob.setup("--thing req")


def test_two_subgroups():
    @dataclass
    class Bob(TestSetup):
        first: Union[Foo, Bar] = subgroups({"foo": Foo, "bar": Bar}, default=Bar(d=3))
        second: Union[Baz, Blop] = subgroups({"baz": Baz, "blop": Blop}, default=Blop())

    # BUG: Can't have `add_help` on the top-level parser...
    parser = ArgumentParser(add_help=True)
    parser.add_arguments(Bob, dest="bob")
    # args = parser.parse_args(["--help"])

    args = parser.parse_args("--thing foo_thing --thing.a 123".split())
    bob = args.bob
    thing = bob.thing
    assert is_dataclass(thing)
    assert thing == Foo(a=123)
