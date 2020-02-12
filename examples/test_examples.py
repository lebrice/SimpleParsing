"""A test to make sure that all the example files work without crashing.
(Could be seen as a kind of integration test.)

"""
import contextlib
import importlib
import shlex
import sys
from io import StringIO
import pytest
from test import xfail_param
from typing import Callable, Optional
expected = ""


@pytest.fixture
def set_prog_name():
    argv = sys.argv.copy()
    del sys.argv[1:]

    def set_prog(prog_name: str, args: str):
        sys.argv[0] = prog_name
        sys.argv[1:] = shlex.split(args)
    yield set_prog
    sys.argv = argv


@pytest.fixture
def assert_equals_stdout(capsys):
    def without_spaces(string): return "".join(string.split())

    def should_equal(expected):
        out = capsys.readouterr().out.strip()
        assert without_spaces(out) == without_spaces(expected)
    return should_equal


@pytest.mark.parametrize(
    "file_path, args",
    [
        ("examples/aliases/aliases_example.py",             ""),
        ("examples/container_types/lists_example.py",       ""),
        ("examples/custom_args/custom_args_example.py",     ""),
        ("examples/dataclasses/dataclass_example.py",       ""),
        ("examples/dataclasses/hyperparameters_example.py", ""),
        ("examples/docstrings/docstrings_example.py",       ""),
        ("examples/enums/enums_example.py",                 ""),
        ("examples/inheritance/inheritance_example.py",     ""),
        ("examples/inheritance/ml_inheritance.py",          ""),
        ("examples/inheritance/ml_inheritance_2.py",        ""),
        ("examples/merging/multiple_example.py",            ""),
        xfail_param("examples/merging/multiple_lists_example.py", "", reason="BUG"),
        ("examples/ML/ml_example_before.py",                ""),
        ("examples/ML/ml_example_after.py",                 ""),
        ("examples/ML/other_ml_example.py",                 ""),
        ("examples/nesting/nesting_example.py",             ""),
        ("examples/prefixing/manual_prefix_example.py",     ""),
        ("examples/simple/simple_example_before.py", "--some_required_int 123"),
        ("examples/simple/simple_example_after.py",  "--some_required_int 123"),
        ("examples/subparsers/subparsers_example.py",       "train"),
        ("examples/ugly/ugly_example_before.py",            ""),
        ("examples/ugly/ugly_example_after.py",             ""),
    ])
def test_running_example_outputs_expected(
        file_path: str,
        args: str,
        set_prog_name: Callable[[str, Optional[str]], None],
        assert_equals_stdout: Callable[[str], None]
):
    script = file_path.split("/")[-1] + ".py"
    set_prog_name(script, args)
    module_name = file_path.replace("/", ".").replace(".py", "")
    # programmatically import the example script, which also runs it.
    # (Equivalent to executing "from <module_name> import expected")
    module = __import__(module_name, globals(), locals(), ["expected"], 0)
    # get the 'expected'
    if hasattr(module, "expected"):
        assert_equals_stdout(module.expected)
