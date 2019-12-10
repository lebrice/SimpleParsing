import argparse
import dataclasses
from dataclasses import dataclass, field
from typing import *

import pytest

from . import TestSetup
from simple_parsing import (Formatter, InconsistentArgumentError,
                            ArgumentParser, ConflictResolution)

from .example_use_cases import *

def test_hparam_use_case():
    hparams = HyperParameters.setup(
        "--num_layers 5 6 7",
        conflict_resolution_mode=ConflictResolution.ALWAYS_MERGE
    )
    assert isinstance(hparams, HyperParameters)
    # print(hparams.get_help_text())
    assert hparams.gender.num_layers == 5
    assert hparams.age_group.num_layers == 6
    assert hparams.personality.num_layers == 7
    
    assert hparams.gender.num_units == 32
    assert hparams.age_group.num_units == 64
    assert hparams.personality.num_units == 8
    
    assert hparams.gender.use_likes == True
    assert hparams.age_group.use_likes == True
    assert hparams.personality.use_likes == False

if __name__ == "__main__":
    hparams = HyperParameters()
    # print(HyperParameters.setup("--help", conflict_resolution_mode=ConflictResolution.EXPLICIT))
    # exit()
    print(hparams.age_group)
    hparams.age_group.num_layers = 123

    hparams = HyperParameters()
    print(hparams.age_group)
    exit()
