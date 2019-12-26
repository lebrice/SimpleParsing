import argparse
import dataclasses
from dataclasses import dataclass, field
from typing import *

import pytest

from . import TestSetup
from simple_parsing import (Formatter, InconsistentArgumentError,
                            ArgumentParser, ConflictResolution)


def test_real_use_case(silent, HyperParameters, TaskHyperParameters):
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
