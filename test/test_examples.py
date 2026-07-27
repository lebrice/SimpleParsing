"""A test to make sure that all the example files work without crashing.

(Could be seen as a kind of integration test.)
"""

from __future__ import annotations

import glob
import os
import runpy
import shlex
import sys
from collections import Counter
from collections.abc import Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

import pytest

from .testutils import needs_yaml

expected = ""


def xfail_param(*args, reason: str):
    return pytest.param(*args, marks=pytest.mark.xfail(reason=reason))


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
    def strip(string):
        return "".join(string.split())

    def should_equal(expected: str, file_path: str):
        if "optional arguments" in expected and sys.version_info >= (3, 10):
            expected = expected.replace("optional arguments", "options")
        out = capsys.readouterr().out
        # assert strip(out) == strip(expected), file_path
        # assert out == expected, file_path
        out_lines = out.splitlines(keepends=False)
        out_lines = [line.strip() for line in out_lines if line and not line.isspace()]
        expected_lines = expected.splitlines(keepends=False)
        expected_lines = [line.strip() for line in expected_lines if line and not line.isspace()]
        # Ordering of values in a `Namespace` object are different!
        expected = Counter("".join(expected_lines))
        actual = Counter("".join(out_lines))
        actual[" "] = 0
        expected[" "] = 0
        assert actual == expected, (
            out_lines,
            expected_lines,
        )

    return should_equal


@pytest.mark.parametrize(
    "file_path, args",
    [
        ("examples/subparsers/subparsers_example.py", "train"),
    ],
)
def test_running_example_outputs_expected(
    file_path: str,
    args: str,
    set_prog_name: Callable[[str, str | None], None],
    assert_equals_stdout: Callable[[str, str], None],
):
    # set_prog_name(script, args)
    example_dir = Path(file_path).parent

    file_path = Path(file_path).as_posix()
    module_name = file_path.replace("/", ".")
    if module_name.endswith(".py"):
        module_name = module_name[:-3]
    # programmatically import the example script, which also runs it.
    # (Equivalent to executing "from <module_name> import expected")

    # move to the example directory.
    with temporarily_chdir(example_dir), temporarily_add_args(args):
        resulting_globals = runpy.run_module(
            module_name, init_globals=None, run_name="__main__", alter_sys=True
        )

    if "expected" not in resulting_globals:
        pytest.xfail(reason="Example doesn't have an 'expected' global variable.")
    expected = resulting_globals["expected"]
    assert_equals_stdout(expected, file_path)


@pytest.mark.parametrize(
    "file_path",
    [
        *[
            pytest.param(
                p,
                marks=(
                    [
                        pytest.mark.skipif(
                            sys.version_info[:2] == (3, 6),
                            reason="Example uses __future__ annotations feature",
                        ),
                        pytest.mark.xfail(
                            reason="Example has different indentation depending on python version.",
                        ),
                    ]
                    if p == "examples/subgroups/subgroups_example.py"
                    else [needs_yaml]
                    if p
                    in [
                        "examples/config_files/one_config.py",
                        "examples/config_files/composition.py",
                        "examples/config_files/many_configs.py",
                        "examples/serialization/serialization_example.py",
                    ]
                    else []
                ),
            )
            for p in glob.glob("examples/**/*.py")
            if p
            not in {
                "examples/merging/multiple_lists_example.py",
                "examples/subparsers/subparsers_example.py",
                "examples/serialization/custom_types_example.py",
            }
        ],
    ],
)
def test_running_example_outputs_expected_without_arg(
    file_path: str,
    set_prog_name: Callable[[str, str | None], None],
    assert_equals_stdout: Callable[[str, str], None],
):
    return test_running_example_outputs_expected(
        file_path, "", set_prog_name, assert_equals_stdout
    )


@contextmanager
def temporarily_chdir(new_dir: Path):
    """Temporarily navigate to the given directory."""
    start_dir = Path.cwd()
    try:
        os.chdir(new_dir)
        yield
    except OSError:
        raise
    finally:
        os.chdir(start_dir)


@contextmanager
def temporarily_add_args(args: str | Sequence[str]):
    """Temporarily adds the given arguments to sys.argv."""
    if isinstance(args, str):
        args = shlex.split(args)
    start_argv = sys.argv.copy()
    try:
        sys.argv = start_argv + list(args)
        yield
    finally:
        sys.argv = start_argv
