import argparse
import contextlib
import dataclasses
import inspect
import textwrap
from dataclasses import dataclass, fields
from enum import Enum
from typing import *

import pytest
import simple_parsing
import test
from .testutils import TestSetup, xfail

from simple_parsing.utils import subparsers


@dataclass
class TrainOptions:
    """ Training Options """
    lr: float = 1e-3
    train_path: str = "train"

@dataclass
class ValidOptions:
    """ Validation Options """
    test_path: str = "test"
    metric: str = "accuracy"

@dataclass
class GlobalOptions(TestSetup):
    """ Global Options """
    # mode, either Train or Valid.
    mode: Union[TrainOptions, ValidOptions] = subparsers({
        "train": TrainOptions,
        "valid": ValidOptions,
    }, default="train")
    global_arg: str = "something"


def test_required_subparser():
    options = GlobalOptions.setup("train --lr 0.1 --train_path bob")
    assert isinstance(options.mode, TrainOptions)
    assert options.mode.lr == 0.1
    assert options.mode.train_path == "bob"

    options = GlobalOptions.setup("valid --metric some_metric --test_path john")
    assert isinstance(options.mode, ValidOptions)
    assert options.mode.metric == "some_metric"
    assert options.mode.test_path == "john"

@xfail(reason="Invoking --help on the parent parser fails, because of the Parser's Formatter class and a metavar issue.")
def test_help_text_works():
    from contextlib import suppress
    with suppress(SystemExit):
        GlobalOptions.setup("--help")
        GlobalOptions.setup("train --help")


if __name__ == "__main__":
    options = GlobalOptions.setup("train --help")
    print(options)