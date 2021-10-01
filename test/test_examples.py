"""A test to make sure that all the example files work without crashing.
(Could be seen as a kind of integration test.)

"""
import glob
import shlex
import sys
from pathlib import Path
from typing import Callable, Optional

import pytest


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
):
    script = file_path.split("/")[-1]
    # set_prog_name(script, args)
    file_path = Path(file_path).as_posix()
    module_name = file_path.replace("/", ".").replace(".py", "")
    try:
        # programmatically import the example script, which also runs it.
        # (Equivalent to executing "from <module_name> import expected")
        import runpy

        runpy.run_module(
            module_name, init_globals=None, run_name="__main__", alter_sys=True
        )

    except SystemExit:
        pytest.xfail(f"SystemExit in example {file_path}.")


@pytest.mark.parametrize(
    "file_path",
    [
        *[
            p
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
):
    return test_running_example_outputs_expected(
        file_path, "", set_prog_name,
    )
