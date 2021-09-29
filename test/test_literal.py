from dataclasses import dataclass

from .testutils import *

# Not using simple_attribute because floats are disallowed in Literals
# and booleans don't make sense in this context


try:
    from typing import Literal
except:
    from typing_extensions import Literal


def test_literal_argument_str():
    @dataclass
    class SomeClassStr:
        a: Literal["a", "b"]

    parser = ArgumentParser()
    parser.add_arguments(SomeClassStr, dest="some_class")

    args = parser.parse_args(shlex.split("--a a"))
    assert args == argparse.Namespace(some_class=SomeClassStr(a="a"))

    with exits_and_writes_to_stderr("invalid choice"):
        parser.parse_args(shlex.split("--a c"))

    with raises_missing_required_arg():
        parser.parse_args("")


def test_literal_argument_int():
    @dataclass
    class SomeClassInt:
        a: Literal[123, 456]

    parser = ArgumentParser()
    parser.add_arguments(SomeClassInt, dest="some_class")

    args = parser.parse_args(shlex.split("--a 123"))
    assert args == argparse.Namespace(some_class=SomeClassInt(a=123))

    with exits_and_writes_to_stderr("invalid choice"):
        parser.parse_args(shlex.split("--a 789"))

    with raises(SystemExit):
        parser.parse_args(shlex.split("--a test"))

    with raises_missing_required_arg():
        parser.parse_args("")


def test_literal_optional():
    @dataclass
    class SomeClass:
        a: Optional[Literal[123, 456]] = 123

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest="some_class")

    args = parser.parse_args(shlex.split(""))
    assert args == argparse.Namespace(some_class=SomeClass(a=123))

    args = parser.parse_args(shlex.split("--a"))
    assert args == argparse.Namespace(some_class=SomeClass(a=None))

    args = parser.parse_args(shlex.split("--a 456"))
    assert args == argparse.Namespace(some_class=SomeClass(a=456))

    # args = parser.parse_args(shlex.split('--a None'))
    # assert args == argparse.Namespace(some_class=SomeClass(a=None))
    # args = parser.parse_args(shlex.split('--a none'))
    # assert args == argparse.Namespace(some_class=SomeClass(a=None))


def test_literal_optional_without_default():
    @dataclass
    class SomeClass:
        a: Optional[Literal[123, 456]]

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest="some_class")

    args = parser.parse_args(shlex.split(""))
    assert args == argparse.Namespace(some_class=SomeClass(a=None))

    args = parser.parse_args(shlex.split("--a"))
    assert args == argparse.Namespace(some_class=SomeClass(a=None))

    args = parser.parse_args(shlex.split("--a 123"))
    assert args == argparse.Namespace(some_class=SomeClass(a=123))

    # args = parser.parse_args(shlex.split('--a None'))
    # assert args == argparse.Namespace(some_class=SomeClass(a=None))
    # args = parser.parse_args(shlex.split('--a none'))
    # assert args == argparse.Namespace(some_class=SomeClass(a=None))


@parametrize(
    "list_formatting_function",
    [
        format_list_using_spaces,
        # format_list_using_brackets,
        xfail_param(
            format_list_using_brackets,
            reason="TODO: decide which syntax we want to allow for single lists.",
        ),
        xfail_param(
            format_list_using_double_quotes,
            reason="TODO: decide which syntax we want to allow for single lists.",
        ),
        xfail_param(
            format_list_using_single_quotes,
            reason="TODO: decide which syntax we want to allow for single lists.",
        ),
    ],
)
def test_literal_argument_list(list_formatting_function):
    @dataclass
    class SomeClassInt:
        a: List[Literal[123, 456]]

    parser = ArgumentParser()
    parser.add_arguments(SomeClassInt, dest="some_class")

    args = parser.parse_args(shlex.split(f"--a {list_formatting_function([123])}"))
    assert args == argparse.Namespace(some_class=SomeClassInt(a=[123]))
    args = parser.parse_args(shlex.split(f"--a {list_formatting_function([123, 123])}"))
    assert args == argparse.Namespace(some_class=SomeClassInt(a=[123, 123]))
    args = parser.parse_args(shlex.split(f"--a {list_formatting_function([123, 456])}"))
    assert args == argparse.Namespace(some_class=SomeClassInt(a=[123, 456]))

    args = parser.parse_args(shlex.split(f"--a {list_formatting_function([])}"))
    assert args == argparse.Namespace(some_class=SomeClassInt(a=[]))

    with exits_and_writes_to_stderr("invalid choice"):
        parser.parse_args(shlex.split("--a 789"))

    with raises(SystemExit):
        parser.parse_args(shlex.split("--a test"))

    # TODO: Is this the right behavior? Do we expect an empty list to be specified explicitly?
    with raises_missing_required_arg():
        parser.parse_args("")


def test_literal_argument_tuple():
    @dataclass
    class SomeClassTuple:
        a: Tuple[Literal[123, 456], ...]

    parser = ArgumentParser()
    parser.add_arguments(SomeClassTuple, dest="some_class")

    args = parser.parse_args(shlex.split("--a 123"))
    assert args == argparse.Namespace(some_class=SomeClassTuple(a=(123,)))
    args = parser.parse_args(shlex.split("--a 123 123"))
    assert args == argparse.Namespace(some_class=SomeClassTuple(a=(123, 123)))
    args = parser.parse_args(shlex.split("--a 123 456"))
    assert args == argparse.Namespace(some_class=SomeClassTuple(a=(123, 456)))

    args = parser.parse_args(shlex.split(f"--a"))
    assert args == argparse.Namespace(some_class=SomeClassTuple(a=()))

    with exits_and_writes_to_stderr("invalid choice"):
        parser.parse_args(shlex.split("--a 789"))

    with raises(SystemExit):
        parser.parse_args(shlex.split("--a test"))

    # TODO: Is this the right behavior? Do we expect an empty tuple to be specified explicitly?
    with raises_missing_required_arg():
        parser.parse_args("")
