from __future__ import annotations

import os
import shlex
import string
import sys
from contextlib import contextmanager, redirect_stderr
from io import StringIO
from typing import Any, Callable, List, Self, TypeVar

import pytest

from refactored_parsing.parsing import P, ParsingError, parse
from refactored_parsing.utils.utils import camel_case
from refactored_parsing.types import (
    DataclassT,
    ConflictResolution,
)
from refactored_parsing.parsing import ArgumentParser

xfail = pytest.mark.xfail
parametrize = pytest.mark.parametrize


def xfail_param(*args, reason: str):
    if len(args) == 1 and isinstance(args[0], tuple):
        args = args[0]
    return pytest.param(*args, marks=pytest.mark.xfail(reason=reason))


@contextmanager
def raises(exception: type[Exception] = ParsingError, match=None, code: int | None = None):
    with pytest.raises(exception, match=match):
        yield


@contextmanager
def exits_and_writes_to_stderr(match: str = ""):
    s = StringIO()
    with redirect_stderr(s), raises(SystemExit):
        yield
    s.seek(0)
    err_string = s.read()
    if match:
        assert match in err_string, err_string
    else:
        assert err_string, err_string


@contextmanager
def raises_missing_required_arg(args: str | list[str] = ""):
    args_str = " ".join(args) if isinstance(args, list) else args
    with exits_and_writes_to_stderr("the following arguments are required: " + args_str):
        yield


@contextmanager
def raises_invalid_choice():
    with exits_and_writes_to_stderr("invalid choice:"):
        yield


@contextmanager
def raises_expected_n_args(n: int | str):
    with exits_and_writes_to_stderr(f"expected {n} argument{'s' if n != 1 else ''}"):
        yield


@contextmanager
def raises_unrecognized_args(*args: str):
    with exits_and_writes_to_stderr("unrecognized arguments: " + " ".join(args or [])):
        yield


def assert_help_output_equals(actual: str, expected: str) -> None:
    # Replace the start with `prog`, since the test runner might not always be
    # `pytest`, could also be __main__ when debugging with VSCode
    prog = sys.argv[0].split("/")[-1]
    if prog != "pytest":
        expected = expected.replace("usage: pytest", f"usage: {prog}")
    remove = string.punctuation + string.whitespace

    if "optional arguments" in expected and sys.version_info[:2] >= (3, 10):
        expected = expected.replace("optional arguments", "options")

    actual_str = "".join(actual.split())
    actual_str = actual.translate(str.maketrans("", "", remove))
    expected_str = expected.translate(str.maketrans("", "", remove))
    assert actual_str == expected_str, "\n" + "\n".join([actual_str, expected_str])


T = TypeVar("T")


def using_simple_api() -> bool:
    return os.environ.get("SIMPLE_PARSING_API", "simple") == "simple"


class Parseable:
    @classmethod
    def parse_args(
        cls: type[DataclassT],
        arguments: str | None = "",
        dest: str | None = None,
        default: DataclassT | None = None,
        _parser_type: Callable[P, ArgumentParser] = ArgumentParser,
        *parser_args: P.args,
        **parser_kwargs: P.kwargs,
    ) -> DataclassT:
        """Basic setup for a test.

        Parameters:
            arguments:  The arguments to pass to the parser (default: {""})
            dest: the attribute where the argument should be stored. (default: {None})

        Returns:
            An instance of `cls`.
        """

        # TODO: Add a switch here, that uses either the 'simpler' API: `simple_parsing.parse` or
        # this more verbose API: `simple_parsing.ArgumentParser().parse_args()`
        dest = dest or camel_case(cls.__name__)
        return parse(
            cls,
            args=arguments,
            dest=dest,
            default=default,
            _parser_type=_parser_type,
            *parser_args,
            **parser_kwargs,
        )

    @classmethod
    def setup_multiple(
        cls: type[DataclassT], num_to_parse: int, arguments: str | None = ""
    ) -> tuple[DataclassT, ...]:
        parser = ArgumentParser(conflict_resolution=ConflictResolution.ALWAYS_MERGE)
        class_name = camel_case(cls.__name__)
        for i in range(num_to_parse):
            parser.add_arguments(cls, f"{class_name}_{i}")

        if arguments is None:
            args = parser.parse_args()
        else:
            splits = shlex.split(arguments)
            args = parser.parse_args(splits)

        return tuple(getattr(args, f"{class_name}_{i}") for i in range(num_to_parse))

    @classmethod
    def get_help_text(
        cls: type[Self],
        argv: str | None = None,
        dest: str = "config",
        default: Self | None = None,
        prefix: str = "",
        _parser_type: Callable[P, ArgumentParser] = ArgumentParser,
        *parser_args: P.args,
        **parser_kwargs: P.kwargs,
    ) -> str:
        import contextlib
        from io import StringIO

        f = StringIO()

        if argv is None:
            argv = "--help"
        elif not argv.endswith("--help"):
            argv = argv + " --help"

        with StringIO() as f:
            parser = _parser_type(*parser_args, **parser_kwargs)
            parser.add_arguments(cls, dest=dest, default=default, prefix=prefix)

        with contextlib.suppress(SystemExit), contextlib.redirect_stdout(f):
            _ = cls.parse_args(
                argv,
                _parser_type=_parser_type,
                *parser_args,
                **parser_kwargs,
            )
        s = f.getvalue()
        return s


ListFormattingFunction = Callable[[List[Any]], str]
ListOfListsFormattingFunction = Callable[[List[List[Any]]], str]


def format_list_using_spaces(value_list: list[Any]) -> str:
    return " ".join(str(p) for p in value_list)


def format_list_using_brackets(value_list: list[Any]) -> str:
    return f"[{','.join(str(p) for p in value_list)}]"


def format_list_using_single_quotes(value_list: list[Any]) -> str:
    return f"'{format_list_using_spaces(value_list)}'"


def format_list_using_double_quotes(value_list: list[Any]) -> str:
    return f'"{format_list_using_spaces(value_list)}"'


def format_lists_using_brackets(list_of_lists: list[list[Any]]) -> str:
    return " ".join(format_list_using_brackets(value_list) for value_list in list_of_lists)


def format_lists_using_double_quotes(list_of_lists: list[list[Any]]) -> str:
    return " ".join(format_list_using_double_quotes(value_list) for value_list in list_of_lists)


def format_lists_using_single_quotes(list_of_lists: list[list[Any]]) -> str:
    return " ".join(format_list_using_single_quotes(value_list) for value_list in list_of_lists)
