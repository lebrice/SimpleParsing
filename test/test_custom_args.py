import argparse
import shlex
from dataclasses import dataclass
from typing import Any

import pytest
from simple_parsing import ArgumentParser, field

from .testutils import *
from typing import List

def test_custom_args():
    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(
            default="/out",
            alias=["-o", "--out"],
            choices=["/out", "/bob"]
        )

    foo = Foo.setup("--output_dir /bob")
    assert foo.output_dir == "/bob"

    with raises(SystemExit):
        foo = Foo.setup("-o /cat")
        assert foo.output_dir == "/cat"

    foo = Foo.setup("--out /bob")
    assert foo.output_dir == "/bob"


def test_custom_action_args():
    value = 0

    class CustomAction(argparse.Action):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def __call__(self, parser, namespace, values, dest):
            nonlocal value
            value += 1
            setattr(namespace, self.dest, values)

    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(type=str, nargs="?", action=CustomAction)

    foo = Foo.setup("")
    assert value == 0

    foo = Foo.setup("--output_dir")
    assert value == 1

    foo = Foo.setup("--output_dir blablabob")
    assert value == 2
    assert foo.output_dir == "blablabob"


def test_custom_nargs_int():
    """Shows that you can use 'nargs' with the field() function. """
    @dataclass
    class Foo(TestSetup):
        output_dir: str = field(type=str, nargs=2)

    with raises_expected_n_args(2):
        foo = Foo.setup("--output_dir")

    with raises_expected_n_args(2):
        foo = Foo.setup("--output_dir hey")

    foo = Foo.setup("--output_dir john bob")
    assert foo.output_dir == ["john", "bob"]


def test_custom_nargs_plus():
    @dataclass
    class Foo(TestSetup):
        some_int: int = field(type=int, default=-1, nargs="+")

    with raises_missing_required_arg():
        foo = Foo.setup("")

    with exits_and_writes_to_stderr(match="expected at least one argument"):
        foo = Foo.setup("--some_int")

    foo = Foo.setup("--some_int 123")
    assert foo.some_int == [123]

    foo = Foo.setup("--some_int 123 456")
    assert foo.some_int == [123, 456]


def test_custom_nargs_star():
    @dataclass
    class Foo(TestSetup):
        some_int: int = field(type=int, nargs="*")

    foo = Foo.setup("")
    assert foo.some_int == None

    foo = Foo.setup("--some_int")
    assert foo.some_int == []

    foo = Foo.setup("--some_int 123")
    assert foo.some_int == [123]

    foo = Foo.setup("--some_int 123 456")
    assert foo.some_int == [123, 456]


def test_custom_nargs_question_mark():
    @dataclass
    class Foo(TestSetup):
        some_int: int = field(type=int, default=-1, nargs="?")

    foo = Foo.setup("")
    assert foo.some_int == -1

    foo = Foo.setup("--some_int")
    assert foo.some_int == None

    foo = Foo.setup("--some_int 123")
    assert foo.some_int == 123

    with raises_unrecognized_args("456"):
        foo = Foo.setup("--some_int 123 456")


@dataclass
class Foo:
    flag: bool = field(alias=["-f", "-flag"], action="store_true")
    # wether or not to store some value.
    no_cache: bool = field(action="store_false")


def test_store_true_action(parser: TestParser[Foo]):
    parser.add_arguments(Foo, "foo")
    foo = parser("--flag")
    assert foo.flag == True

    foo = parser("")
    assert foo.flag == False

    foo = parser("-f")
    assert foo.flag == True

    foo = parser("-flag")
    assert foo.flag == True


def test_store_false_action():
    parser = ArgumentParser(add_option_string_dash_variants=True)
    parser.add_arguments(Foo, "foo")

    args = parser.parse_args("--no-cache".split())
    foo: Foo = args.foo
    assert foo.no_cache == False

    args = parser.parse_args("".split())
    foo: Foo = args.foo
    assert foo.no_cache == True


def test_list_of_choices():
    @dataclass
    class Foo(TestSetup):
        """ Some class Foo """

        # A sequence of tasks.
        task_sequence: List[str] = field(choices=["train", "test", "ood"])

    foo = Foo.setup("--task_sequence train train ood")
    assert foo.task_sequence == ["train", "train", "ood"]

    with exits_and_writes_to_stderr(match="invalid choice:"):
        Foo.setup("--task_sequence train bob test")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--foo', action='store_const', const=42)
    args = parser.parse_args()
    print(args)
