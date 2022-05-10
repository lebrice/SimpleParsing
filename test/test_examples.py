"""A test to make sure that all the example files work without crashing.
(Could be seen as a kind of integration test.)

"""
import glob
import shlex
import sys
from collections import Counter
from pathlib import Path
from typing import Callable, Optional

import pytest

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
        if sys.version_info[:2] >= (3, 9):
            # Ordering of values in a `Namespace` object are different!
            expected = Counter("".join(expected_lines))
            actual = Counter("".join(out_lines))
            actual[" "] = 0
            expected[" "] = 0
            assert actual == expected, (
                out_lines,
                expected_lines,
            )
        else:
            assert out_lines == expected_lines, file_path

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
    set_prog_name: Callable[[str, Optional[str]], None],
    assert_equals_stdout: Callable[[str, str], None],
):
    script = file_path.split("/")[-1]
    # set_prog_name(script, args)
    file_path = Path(file_path).as_posix()
    module_name = file_path.replace("/", ".").replace(".py", "")
    try:
        # programmatically import the example script, which also runs it.
        # (Equivalent to executing "from <module_name> import expected")
        import runpy

        resulting_globals = runpy.run_module(
            module_name, init_globals=None, run_name="__main__", alter_sys=True
        )
        # module = __import__(module_name, globals(), locals(), ["expected"], 0)
        # resulting_globals = vars(module)
        # get the 'expected'
        # assert "expected" in resulting_globals
        if "expected" not in resulting_globals:
            pytest.xfail(reason="Example doesn't have an 'expected' global variable.")
        expected = resulting_globals["expected"]
        assert_equals_stdout(expected, file_path)

    except SystemExit as e:
        pytest.xfail(f"SystemExit in example {file_path}.")


@pytest.mark.parametrize(
    "file_path",
    [
        *[
            pytest.param(
                p,
                marks=[
                    pytest.mark.skipif(
                        sys.version_info[:2] == (3, 6),
                        reason="Example uses __future__ annotations feature",
                    ),
                    pytest.mark.xfail(
                        reason="Example has different indentation depending on python version.",
                    ),
                ],
            )
            if p == "examples/subgroups/subgroups_example.py"
            else p
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
    set_prog_name: Callable[[str, Optional[str]], None],
    assert_equals_stdout: Callable[[str, str], None],
):
    return test_running_example_outputs_expected(file_path, "", set_prog_name, assert_equals_stdout)
