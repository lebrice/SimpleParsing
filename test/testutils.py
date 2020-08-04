import argparse
import shlex
import string
import sys
from contextlib import contextmanager, suppress
from typing import (Any, Callable, Dict, Generic, List, Optional, Tuple, Type,
                    TypeVar, cast)

import pytest

import simple_parsing
from simple_parsing import (ArgumentParser, ConflictResolution,
                            InconsistentArgumentError, ParsingError,
                            SimpleHelpFormatter)
from simple_parsing.utils import camel_case
from simple_parsing.wrappers import DataclassWrapper

xfail = pytest.mark.xfail
parametrize = pytest.mark.parametrize


def xfail_param(*args, reason: str):
    return pytest.param(*args, marks=pytest.mark.xfail(reason=reason))


Dataclass = TypeVar("Dataclass")


@contextmanager
def raises(exception=ParsingError, match=None, code: int=None):
    with pytest.raises(exception, match=match):
        yield


@contextmanager
def raises_missing_required_arg():
    with raises(match="the following arguments are required"):
        yield


@contextmanager
def raises_expected_n_args(n: int):
    with raises(match=f"expected {n} arguments"):
        yield


@contextmanager
def raises_unrecognized_args(*args: str):
    with raises(match=f"unrecognized arguments: " + " ".join(args or [])):
        yield


def assert_help_output_equals(actual: str, expected: str) -> bool:
    # Replace the start with `prog`, since the test runner might not always be
    # `pytest`, could also be __main__ when debugging with VSCode
    prog = sys.argv[0].split("/")[-1]
    if prog != "pytest":
        expected = expected.replace("usage: pytest", f"usage: {prog}")
    remove = string.punctuation + string.whitespace
    assert "".join(actual.split()) == "".join(expected.split())


T = TypeVar("T")


class TestParser(simple_parsing.ArgumentParser, Generic[T]):
    __test__ = False
    """ A parser subclass just used for testing.
    Makes the retrieval of the arguments a bit easier to read.
    """

    def __init__(self, *args, **kwargs):
        self._current_dest = None
        self._current_dataclass = None
        super().__init__(*args, **kwargs)

    def add_arguments(self, dataclass: Type, dest, prefix='', default=None):
        if self._current_dest == dest and self._current_dataclass == dataclass:
            return  # already added arguments for that dataclass.
        self._current_dest = dest
        self._current_dataclass = dataclass
        return super().add_arguments(
            dataclass,
            dest,
            prefix=prefix,
            default=default
        )

    def __call__(self, args: str) -> T:
        namespace = self.parse_args(shlex.split(args))
        value = getattr(namespace, self._current_dest)
        value = cast(T, value)
        return value


class TestSetup():
    @classmethod
    def setup(cls: Type[Dataclass],
              arguments: Optional[str] = "",
              dest: Optional[str] = None,
              default: Optional[Dataclass] = None,
              conflict_resolution_mode: ConflictResolution = ConflictResolution.AUTO,
              add_option_string_dash_variants: bool = False,
              parse_known_args: bool=False,
              attempt_to_reorder: bool=False,
              ) -> Dataclass:
        """Basic setup for a test.

        Keyword Arguments:
            arguments {Optional[str]} -- The arguments to pass to the parser (default: {""})
            dest {Optional[str]} -- the attribute where the argument should be stored. (default: {None})

        Returns:
            {cls}} -- the class's type.
        """
        parser = simple_parsing.ArgumentParser(
            conflict_resolution=conflict_resolution_mode,
            add_option_string_dash_variants=add_option_string_dash_variants,
        )
        if dest is None:
            dest = camel_case(cls.__name__)

        parser.add_arguments(cls, dest=dest, default=default)

        if arguments is None:
            if parse_known_args:
                args = parser.parse_known_args(attempt_to_reorder=attempt_to_reorder)
            else:
                args = parser.parse_args()
        else:
            splits = shlex.split(arguments)
            if parse_known_args:
                args, unknown_args = parser.parse_known_args(splits, attempt_to_reorder=attempt_to_reorder)
            else:
                args = parser.parse_args(splits)
        assert hasattr(
            args, dest), f"attribute '{dest}' not found in args {args}"
        instance: Dataclass = getattr(args, dest)  # type: ignore
        delattr(args, dest)
        assert args == argparse.Namespace(
        ), f"Namespace has leftover garbage values: {args}"

        instance = cast(Dataclass, instance)
        return instance

    @classmethod
    def setup_multiple(cls: Type[Dataclass], num_to_parse: int, arguments: Optional[str] = "") -> Tuple[Dataclass, ...]:
        conflict_resolution_mode: ConflictResolution = ConflictResolution.ALWAYS_MERGE

        parser = simple_parsing.ArgumentParser(
            conflict_resolution=conflict_resolution_mode)
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
    def get_help_text(cls, multiple=False, conflict_resolution_mode: ConflictResolution = ConflictResolution.AUTO) -> str:
        import contextlib
        from io import StringIO
        f = StringIO()
        with contextlib.suppress(SystemExit), contextlib.redirect_stdout(f):
            _ = cls.setup(
                "--help", conflict_resolution_mode=conflict_resolution_mode)
        s = f.getvalue()
        return s


ListFormattingFunction = Callable[[List[Any]], str]
ListOfListsFormattingFunction = Callable[[List[List[Any]]], str]


def format_list_using_spaces(value_list: List[Any])-> str:
    return " ".join(str(p) for p in value_list)


def format_list_using_brackets(value_list: List[Any])-> str:
    return f"[{','.join(str(p) for p in value_list)}]"


def format_list_using_single_quotes(value_list: List[Any])-> str:
    return f"'{format_list_using_spaces(value_list)}'"


def format_list_using_double_quotes(value_list: List[Any])-> str:
    return f'"{format_list_using_spaces(value_list)}"'


def format_lists_using_brackets(list_of_lists: List[List[Any]])-> str:
    return " ".join(
        format_list_using_brackets(value_list)
        for value_list in list_of_lists
    )


def format_lists_using_double_quotes(list_of_lists: List[List[Any]])-> str:
    return " ".join(
        format_list_using_double_quotes(value_list)
        for value_list in list_of_lists
    )


def format_lists_using_single_quotes(list_of_lists: List[List[Any]])-> str:
    return " ".join(
        format_list_using_single_quotes(value_list)
        for value_list in list_of_lists
    )
