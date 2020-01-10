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

from .testutils import TestSetup

from simple_parsing.utils import subparsers

@dataclass
class TrainOptions:
    lr: float = 1e-3
    train_path: str = "train"

@dataclass
class TestOptions:
    test_path: str = "test"
    metric: str = "accuracy"

@dataclass
class GlobalOptions(TestSetup):
    mode: Union[TrainOptions, TestOptions] = subparsers({
        "train": TrainOptions,
        "test": TestOptions,
    }, default="train")
    global_arg: str = "something"


def test_required_subparser():
    
    options = GlobalOptions.setup("train --lr 0.1 --train_path bob".split())
    assert isinstance(options.mode, )