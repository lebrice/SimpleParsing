import argparse
import dataclasses
from dataclasses import dataclass, field
from typing import *

import pytest

from . import TestSetup
from simple_parsing import (Formatter, InconsistentArgumentError,
                            ArgumentParser, ConflictResolution)

from .example_use_cases import HyperParameters

def test_real_use_case(no_warnings, no_stdout):
    hparams = HyperParameters.setup(
        "--age_group.num_layers 5 "
        "--age_group.num_units 65 "
        ,
        conflict_resolution_mode=ConflictResolution.AUTO
    )
    assert isinstance(hparams, HyperParameters)
    # print(hparams.get_help_text())
    assert hparams.gender.num_layers == 1
    assert hparams.gender.num_units == 32
    assert hparams.age_group.num_layers == 5
    assert hparams.age_group.num_units == 65
    assert hparams.age_group.use_likes == True

if __name__ == "__main__":
    hparams = HyperParameters()
    # print(HyperParameters.setup("--help", conflict_resolution_mode=ConflictResolution.EXPLICIT))
    # exit()
    print(hparams.age_group)
    hparams.age_group.num_layers = 123

    hparams = HyperParameters()
    print(hparams.age_group)
    exit()
