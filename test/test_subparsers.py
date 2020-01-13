import argparse
import contextlib
import dataclasses
import inspect
import test
import textwrap
from dataclasses import dataclass, fields
from enum import Enum
from pathlib import Path
from typing import *

import pytest

import simple_parsing
from simple_parsing.utils import subparsers

from .testutils import TestSetup, xfail


@dataclass
class TrainOptions:
    """ Training Options """
    lr: float = 1e-3
    train_path: Path = Path("./train")

@dataclass
class ValidOptions:
    """ Validation Options """
    test_path: Path = Path("./test")
    metric: str = "accuracy"

@dataclass
class GlobalOptions(TestSetup):
    """ Global Options """
    # mode, either Train or Valid.
    mode: Union[TrainOptions, ValidOptions] = subparsers({
        "train": TrainOptions,
        "valid": ValidOptions,
    })
    global_arg: str = "something"

# options = GlobalOptions.setup("--global_arg 123 --help")
# print(options)
# exit()

def test_required_subparser():
    options = GlobalOptions.setup("train --lr 0.1 --train_path ./bob")
    assert isinstance(options.mode, TrainOptions)
    assert options.mode.lr == 0.1
    assert options.mode.train_path == Path("./bob")

    options = GlobalOptions.setup("valid --metric some_metric --test_path ./john")
    assert isinstance(options.mode, ValidOptions)
    assert options.mode.metric == "some_metric"
    assert options.mode.test_path == Path("./john")

def test_help_text_works():
    from contextlib import suppress
    with suppress(SystemExit):
        GlobalOptions.setup("--help")
        GlobalOptions.setup("train --help")

@dataclass
class Start:
    """Start command"""
    value: str = "start command value"

    def execute(self, verbose=False):
        print(f"Start (verbose: {verbose})")
        return self.value

@dataclass
class Stop:
    """Stop command"""
    value: str = "stop commmand value"

    def execute(self, verbose=False):
        print(f"Stop (verbose: {verbose})")
        return self.value

@dataclass
class Push:
    """Example of a subcommand."""
    subcommand: Union[Start, Stop]
    some_flag_1: str = "command1"

    def execute(self, verbose=False):
        print(f"Push (verbose: {verbose})")
        return self.subcommand.execute(verbose=verbose)


@dataclass
class Pull:
    """Other Example of a subcommand."""
    subcommand: Union[Start, Stop]
    some_flag_2: str = "command2"

    def execute(self, verbose=False):
        print(f"Pull (verbose: {verbose})")
        return self.subcommand.execute(verbose=verbose)


@dataclass
class Program(TestSetup):
    """Some top-level command"""
    command: Union[Push, Pull]
    verbose: bool = False

    def execute(self):
        print(f"Program (verbose: {self.verbose})")
        return self.command.execute(verbose=self.verbose)


def test_command_tree():
    prog: Program = Program.setup("push start --value jack")
    assert isinstance(prog.command, Push)
    assert isinstance(prog.command.subcommand, Start)
    assert prog.command.subcommand.value == "jack"
    assert prog.execute() == "jack"


if __name__ == "__main__":
    import sys
    print("ARGS:", " ".join(sys.argv[1:]))
    prog: Program = Program.setup(" ".join(sys.argv[1:]))
    print(prog)
    print(prog.execute())
    exit()
