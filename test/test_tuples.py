import shlex
import sys
import textwrap
from dataclasses import dataclass
from typing import Any, Optional, Union

import pytest

from simple_parsing import ArgumentParser

from .testutils import (
    TestSetup,
    assert_help_output_equals,
    raises_unrecognized_args,
    xfail_param,
)


def test_tuple_any_becomes_string():
    @dataclass
    class Container(TestSetup):
        strings: tuple = (64, 128, 256, 512)

    c = Container.setup("")
    assert c.strings == (64, 128, 256, 512)
    c = Container.setup("--strings 12 24 36")
    assert c.strings == ("12", "24", "36")


def test_tuple_with_n_items_takes_only_n_values():
    @dataclass
    class Container(TestSetup):
        ints: tuple[int, int] = (1, 5)

    c = Container.setup("")
    assert c.ints == (1, 5)
    with raises_unrecognized_args("6", "7", "8"):
        c = Container.setup("--ints 4 5 6 7 8")


def test_tuple_elipsis_takes_any_number_of_args():
    @dataclass
    class Container(TestSetup):
        ints: tuple[int, ...] = (1, 2, 3)

    c = Container.setup("")
    assert c.ints == (1, 2, 3)
    c = Container.setup("--ints 4 5 6 7 8")
    assert c.ints == (4, 5, 6, 7, 8)


@pytest.mark.skipif(
    sys.version_info != (3, 12), reason="Output format differs between Python versions."
)
def test_tuple_with_ellipsis_help_format():
    @dataclass
    class Container(TestSetup):
        ints: tuple[int, ...] = (1, 2, 3)

    assert Container.get_help_text() == textwrap.dedent(
        """\
        usage: pytest [-h] [--ints int [int, ...]]

        options:
          -h, --help            show this help message and exit

        test_tuple_with_ellipsis_help_format.<locals>.Container ['container']:
          Container(ints: Tuple[int, ...] = (1, 2, 3))

          --ints int [int, ...]   (default: (1, 2, 3))
        """,
    )


def test_each_type_is_used_correctly():
    @dataclass
    class Container(TestSetup):
        """A container with mixed items in a tuple."""

        mixed: tuple[int, str, bool, float] = (1, "bob", False, 1.23)

    c = Container.setup("")
    assert c.mixed == (1, "bob", False, 1.23)

    c = Container.setup("--mixed 1 2 0 1")
    assert c.mixed == (1, "2", False, 1.0)

    assert_help_output_equals(
        Container.get_help_text(),
        """
    usage: pytest [-h] [--mixed int str bool float]

    optional arguments:
    -h, --help            show this help message and exit

    test_each_type_is_used_correctly.<locals>.Container ['container']:
    A container with mixed items in a tuple.

      --mixed int str bool float   (default: (1, 'bob', False, 1.23))
    """,
    )


def test_issue_29():
    from simple_parsing import ArgumentParser

    @dataclass
    class MyCli:
        asdf: tuple[str, ...]

    parser = ArgumentParser()
    parser.add_arguments(MyCli, dest="args")
    args = parser.parse_args("--asdf asdf fgfh".split())
    assert args.args == MyCli(asdf=("asdf", "fgfh"))


# 'sentinel' object used when parametrizing tests below to indicate that the option
# string shouldn't be passed at all, rather than have no passed value: so that
# `parser.parse_args("")` is used instead of `parse_args("--foo")`.
DONT_PASS = object()


@dataclass
class MyConfig:
    values: Optional[tuple[int, int]]


class TestIssue47:
    @pytest.mark.xfail(reason="Will fail once the issue if solved.")
    def test_reproduce(self):
        parser = ArgumentParser()
        parser.add_arguments(MyConfig, dest="cfg")
        args_none, _ = parser.parse_known_args([])
        args, extra = parser.parse_known_args(["--values", "3", "4"])
        values = args.cfg.values
        # This is what we'd expect:
        # assert values == (3, 4)
        # assert extra == []

        # But instead we get this:
        assert values == (3)
        assert extra == ["4"]

    @pytest.mark.parametrize(
        "options, passed_arg, expected_value",
        [
            (dict(type=int, nargs=2, required=True), "1 2", [1, 2]),
            (dict(nargs=2, required=False), "1 3", ["1", "3"]),
            (dict(nargs=2, required=False), DONT_PASS, None),
            (dict(nargs="?", required=False, const=[]), " ", []),
            (dict(nargs="*", type=int, required=True), "1 2 3", [1, 2, 3]),
            (dict(type=int, nargs="*", required=True), "1 2 3", [1, 2, 3]),
        ],
    )
    def test_vanilla_argparse_beheviour(
        self, options: dict[str, Any], passed_arg: str, expected_value: Any
    ):
        parser = ArgumentParser()
        parser.add_argument("--foo", **options)

        if passed_arg is DONT_PASS:
            args = parser.parse_args("")
        else:
            args = parser.parse_args(shlex.split("--foo " + passed_arg))
        foo = args.foo
        assert foo == expected_value

    @pytest.mark.parametrize(
        "field_type, expected_options",
        [
            (tuple[str, str], dict(type=str, nargs=2, required=True)),
            # A Weirder 'type' will be generated for this one:
            (tuple[str, int], dict(nargs=2, required=True)),
            (Optional[tuple[str, str]], dict(nargs=2, required=False)),
            (Optional[tuple[str, str]], dict(nargs=2, required=False)),
            xfail_param(
                *(Optional[list[str]], dict(nargs="*", required=False, const=[])),
                reason="Can't use 'const' with nargs of '*'.",
            ),
            (list[str], dict(type=str, nargs="*", required=True)),
        ],
    )
    def test_arg_options_created(self, field_type: type, expected_options: dict[str, Any]):
        """Check the 'arg_options' that get created for different types of tuple fields."""
        parser = ArgumentParser()

        @dataclass
        class MyConfig:
            values: field_type

        parser.add_arguments(MyConfig, dest="config")
        parser._preprocessing()
        field_wrapper = parser._wrappers[0].fields[0]
        generated_options = field_wrapper.arg_options
        for option, expected_value in expected_options.items():
            actual_value = generated_options[option]
            assert actual_value == expected_value

    @pytest.mark.parametrize(
        "field_type, passed_arg, expected_value",
        [
            (tuple[str, str], "a b", ("a", "b")),
            (Optional[tuple[str, str]], DONT_PASS, None),
            (Optional[tuple[str, str]], "a b", ("a", "b")),
            (Optional[tuple[str, int]], "a 1", ("a", 1)),
            (Optional[tuple[str, int, bool]], DONT_PASS, None),
            (Optional[tuple[str, int, bool]], "a 1 1", ("a", 1, True)),
            (tuple[str, int, bool], "a 1 1", ("a", 1, True)),
            # TODO: Issue #42 Add better support for Nested tuples:
            xfail_param(
                *(
                    tuple[tuple[str, int], tuple[float, bool]],
                    "a 1 2. 1",  # 'flat' version:
                    (("a", 1), (2.0, True)),
                ),
                reason="TODO: Issue #42 Add better support for Nested tuples",
            ),
            xfail_param(
                *(
                    tuple[tuple[str, int], tuple[float, bool]],
                    "(a,1) (2.,1)",  # 'nice' version
                    (("a", 1), (2.0, True)),
                ),
                reason="TODO: Issue #42 Add better support for Nested tuples",
            ),
            xfail_param(
                *(
                    tuple[tuple[str, int], tuple[float, bool]],
                    "'(a, 1)' '(2.1, 1)'",  # 'nice' (since quotes are used)
                    (("a", 1), (2.0, True)),
                ),
                reason="TODO: Issue #42 Add better support for Nested tuples",
            ),
            xfail_param(
                *(
                    tuple[tuple[str, int], tuple[float, bool]],
                    "(a, 1) (2.1, 1)",  # not nice, quotes aren't used and there are spaces.
                    (("a", 1), (2.0, True)),
                ),
                reason="TODO: Issue #42 Add better support for Nested tuples",
            ),
        ],
    )
    def test_issue_47_is_fixed(
        self,
        field_type: type,
        passed_arg: Union[str, object],
        expected_value: Any,
    ):
        parser = ArgumentParser()

        @dataclass
        class MyConfig:
            values: field_type

        parser.add_arguments(MyConfig, dest="config")
        if passed_arg is DONT_PASS:
            args = parser.parse_args([])
        else:
            args = parser.parse_args(shlex.split("--values " + passed_arg))
        actual_values = args.config.values
        assert actual_values == expected_value

    @pytest.mark.parametrize(
        "passed_arg, expected_value",
        [
            (DONT_PASS, None),
            ("", []),
            ("abc", ["abc"]),
            ("abc def", ["abc", "def"]),
        ],
    )
    def test_optional_list(self, passed_arg: str, expected_value: Any):
        parser = ArgumentParser()

        @dataclass
        class MyConfig:
            foo: Optional[list[str]] = None

        parser.add_arguments(MyConfig, dest="config")

        if passed_arg is DONT_PASS:
            args = parser.parse_args("")
        else:
            args = parser.parse_args(shlex.split("--foo " + passed_arg))
        assert args.config.foo == expected_value
