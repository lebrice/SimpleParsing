"""A test to make sure that all the example files work without crashing.
(Could be seen as a kind of integration test.)

"""
import contextlib
import glob
import importlib
import shlex
import sys
from io import StringIO
from test import xfail_param
from typing import Callable, Optional
from pathlib import Path
import pytest

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
    def strip(string): return "".join(string.split())

    def should_equal(expected: str, file_path: str):
        out = capsys.readouterr().out
        assert strip(out) == strip(expected), file_path
    return should_equal


@pytest.mark.parametrize(
    "file_path, args",
    [
        ("examples/subparsers/subparsers_example.py",       "train"),
    ])
def test_running_example_outputs_expected(
        file_path: str,
        args: str,
        set_prog_name: Callable[[str, Optional[str]], None],
        assert_equals_stdout: Callable[[str, str], None]
):
    script = file_path.split("/")[-1]
    set_prog_name(script, args)
    file_path = Path(file_path).as_posix()
    module_name = file_path.replace("/", ".").replace(".py", "")
    try:
        # programmatically import the example script, which also runs it.
        # (Equivalent to executing "from <module_name> import expected")
        module = __import__(module_name, globals(), locals(), ["expected"], 0)
        # get the 'expected'
        if hasattr(module, "expected"):
            assert_equals_stdout(module.expected, file_path)
    except SystemExit as e:
        pytest.xfail(f"SystemExit in example {file_path}.")


@pytest.mark.parametrize(
    "file_path",
    [
        *[p for p in glob.glob("examples/**/*.py") if p not in {
            "examples/merging/multiple_lists_example.py",
            "examples/subparsers/subparsers_example.py",
        }],
        xfail_param("examples/merging/multiple_lists_example.py", reason="BUG"),
    ])
def test_running_example_outputs_expected_without_arg(
        file_path: str,
        set_prog_name: Callable[[str, Optional[str]], None],
        assert_equals_stdout: Callable[[str, str], None]
):
    return test_running_example_outputs_expected(
        file_path,
        "",
        set_prog_name,
        assert_equals_stdout
    )