from __future__ import annotations

import importlib.util
import os
import shlex
import string
import sys
from contextlib import contextmanager, redirect_stderr
from io import StringIO
from typing import Any, Callable, Generic, TypeVar, cast

import pytest

import simple_parsing
from simple_parsing import ConflictResolution, DashVariant, ParsingError
from simple_parsing.utils import camel_case
from simple_parsing.wrappers.field_wrapper import ArgumentGenerationMode, NestedMode

xfail = pytest.mark.xfail
parametrize = pytest.mark.parametrize


def xfail_param(*args, reason: str):
    if len(args) == 1 and isinstance(args[0], tuple):
        args = args[0]
    return pytest.param(*args, marks=pytest.mark.xfail(reason=reason))


Dataclass = TypeVar("Dataclass")


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


class TestParser(simple_parsing.ArgumentParser, Generic[T]):
    __test__ = False
    """A parser subclass just used for testing.

    Makes the retrieval of the arguments a bit easier to read.
    """

    def __init__(self, *args, **kwargs):
        self._current_dest = None
        self._current_dataclass = None
        super().__init__(*args, **kwargs)

    def add_arguments(self, dataclass: type, dest, prefix="", default=None):
        if self._current_dest == dest and self._current_dataclass == dataclass:
            return  # already added arguments for that dataclass.
        self._current_dest = dest
        self._current_dataclass = dataclass
        return super().add_arguments(dataclass, dest, prefix=prefix, default=default)

    def __call__(self, args: str) -> T:
        namespace = self.parse_args(shlex.split(args))
        value = getattr(namespace, self._current_dest)
        value = cast(T, value)
        return value


def using_simple_api() -> bool:
    return os.environ.get("SIMPLE_PARSING_API", "simple") == "simple"


class TestSetup:
    @classmethod
    def setup(
        cls: type[Dataclass],
        arguments: str | None = "",
        dest: str | None = None,
        default: Dataclass | None = None,
        conflict_resolution_mode: ConflictResolution = ConflictResolution.AUTO,
        add_option_string_dash_variants: DashVariant = DashVariant.AUTO,
        parse_known_args: bool = False,
        attempt_to_reorder: bool = False,
        *,
        argument_generation_mode: ArgumentGenerationMode = ArgumentGenerationMode.FLAT,
        nested_mode: NestedMode = NestedMode.DEFAULT,
        **kwargs,
    ) -> Dataclass:
        """Basic setup for a test.

        Keyword Arguments:
            arguments {Optional[str]} -- The arguments to pass to the parser (default: {""})
            dest {Optional[str]} -- the attribute where the argument should be stored. (default: {None})

        Returns:
            {cls}} -- the class's type.
        """

        # TODO: Add a switch here, that uses either the 'simpler' API: `simple_parsing.parse` or
        # this more verbose API: `simple_parsing.ArgumentParser().parse_args()`
        dest = dest or camel_case(cls.__name__)

        if using_simple_api():
            common_kwargs = dict(
                config_class=cls,
                config_path=None,
                args=arguments,
                default=default,
                add_config_path_arg=None,
                nested_mode=nested_mode,
                dest=dest,
                add_option_string_dash_variants=add_option_string_dash_variants,
                conflict_resolution=conflict_resolution_mode,
                argument_generation_mode=argument_generation_mode,
            )
            if parse_known_args:
                instance, unknown_args = simple_parsing.parse_known_args(
                    **common_kwargs,
                    attempt_to_reorder=attempt_to_reorder,
                    **kwargs,
                )
            else:
                instance = simple_parsing.parse(**common_kwargs, **kwargs)
        else:
            parser = simple_parsing.ArgumentParser(
                conflict_resolution=conflict_resolution_mode,
                add_option_string_dash_variants=add_option_string_dash_variants,
                argument_generation_mode=argument_generation_mode,
                nested_mode=nested_mode,
                **kwargs,
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
                    args, unknown_args = parser.parse_known_args(
                        splits, attempt_to_reorder=attempt_to_reorder
                    )
                else:
                    args = parser.parse_args(splits)
            assert hasattr(args, dest), f"attribute '{dest}' not found in args {args}"
            instance: Dataclass = getattr(args, dest)  # type: ignore
            delattr(args, dest)

            # If there are subgroups, we can allow an extra "subgroups" attribute, otherwise we don't
            # expect any other arguments.
            args_dict = vars(args).copy()
            args_dict.pop("subgroups", None)

            assert (
                not args_dict
            ), f"Namespace has leftover garbage values (besides subgroups): {args}"

        instance = cast(Dataclass, instance)
        return instance

    @classmethod
    def setup_multiple(
        cls: type[Dataclass], num_to_parse: int, arguments: str | None = ""
    ) -> tuple[Dataclass, ...]:
        conflict_resolution_mode: ConflictResolution = ConflictResolution.ALWAYS_MERGE

        parser = simple_parsing.ArgumentParser(conflict_resolution=conflict_resolution_mode)
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
        cls,
        argv: str | None = None,
        multiple=False,
        conflict_resolution_mode: ConflictResolution = ConflictResolution.AUTO,
        add_option_string_dash_variants=DashVariant.AUTO,
        **parser_kwargs,
    ) -> str:
        import contextlib
        from io import StringIO

        f = StringIO()

        if argv is None:
            argv = "--help"
        elif not argv.endswith("--help"):
            argv = argv + " --help"

        with contextlib.suppress(SystemExit), contextlib.redirect_stdout(f):
            _ = cls.setup(
                argv,
                conflict_resolution_mode=conflict_resolution_mode,
                add_option_string_dash_variants=add_option_string_dash_variants,
                **parser_kwargs,
            )
        s = f.getvalue()
        return s


ListFormattingFunction = Callable[[list[Any]], str]
ListOfListsFormattingFunction = Callable[[list[list[Any]]], str]


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


YAML_INSTALLED = importlib.util.find_spec("yaml") is not None
needs_yaml = pytest.mark.xfail(
    not YAML_INSTALLED,
    raises=ModuleNotFoundError,
    reason="Test requires pyyaml to be installed.",
)

TOML_INSTALLED = (
    importlib.util.find_spec("tomli") is not None
    and importlib.util.find_spec("tomli_w") is not None
)
needs_toml = pytest.mark.xfail(
    not TOML_INSTALLED,
    raises=ModuleNotFoundError,
    reason="Test requires tomli and tomli_w to be installed.",
)
