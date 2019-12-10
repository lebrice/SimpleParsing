import argparse
import dataclasses
from dataclasses import dataclass, field
from typing import *

import pytest

from . import TestSetup
from simple_parsing import (Formatter, InconsistentArgumentError,
                            ArgumentParser, ConflictResolution)

from .example_use_cases import HyperParameters, TaskHyperParameters

def test_real_use_case():
    default = HyperParameters()
    hparams = HyperParameters.setup(
        "--hyper_parameters.age_group.num_layers 5",
        conflict_resolution_mode=ConflictResolution.EXPLICIT
    )
    assert isinstance(hparams, HyperParameters)
    # print(hparams.get_help_text())
    assert hparams.age_group.num_layers == 5
    assert hparams.gender.num_layers == 1
    assert hparams.gender.num_units == 32
    assert isinstance(hparams.age_group, TaskHyperParameters)
    assert hparams.age_group.use_likes == True

if __name__ == "__main__":
    hparams = HyperParameters()
    print(HyperParameters.setup("--help", conflict_resolution_mode=ConflictResolution.EXPLICIT))
    exit()
    print(hparams.age_group)
    hparams.age_group.num_layers = 123

    hparams = HyperParameters()
    print(hparams.age_group)
    exit()
