import argparse
import dataclasses
from dataclasses import dataclass, field
from typing import *

import pytest

from .testutils import TestSetup
from simple_parsing import (Formatter, InconsistentArgumentError,
                            ArgumentParser, ConflictResolution)

@dataclass
class TaskModelParams():
    """ Settings for a Model for one of the tasks to be completed. """
    num_layers: int = 1 # the number of layers to use
    num_units: int = 32 # the number of dense units
    use_batchnorm: bool = False # wether or not Batch Normalization is to be used
    use_dropout: bool = False # wether or not Dropout is to be used
    dropout_rate: float = 0.1 # the dropout rate
    use_likes: bool = False # wether or not to use the likes as an input to the model
    likes_condensing_layers: int = 0 # the number of layers in the model's like-condensing block
    likes_condensing_units: int = 0 # the number of neurons in the likes condensing block.


@dataclass
class HyperParameters(TestSetup):
    """Hyperparameters of our model."""
    # the batch size
    batch_size: int = 128
    
    # the activation function used after each dense layer
    activation: str = "tanh"
    # Which optimizer to use during training.
    optimizer: str = "sgd"
    # Learning Rate
    learning_rate: float = 0.005

    # L1 regularization coefficient
    l1_reg: float = 0.005
    # L2 regularization coefficient
    l2_reg: float = 0.005

    # number of individual 'pages' that were kept during preprocessing of the 'likes'.
    # This corresponds to the number of entries in the multi-hot like vector.
    num_like_pages: int = 5_000


    gender_loss_weight: float = 1.0
    age_loss_weight: float = 1.0


    num_text_features: ClassVar[int] = 91
    num_image_features: ClassVar[int] = 63

    # Gender model settings:
    gender: TaskModelParams = dataclasses.field(default_factory=lambda: TaskModelParams(num_layers=1, num_units=32, use_likes=False))

    # Age Group Model settings:
    age_group: TaskModelParams = dataclasses.field(default_factory=lambda: TaskModelParams(num_layers=2, num_units=64, use_likes=True, likes_condensing_layers=1, likes_condensing_units=16))
    
    # Personality Model(s) settings:
    personality: TaskModelParams = dataclasses.field(default_factory=lambda: TaskModelParams(num_layers=1, num_units=8, use_likes=False))

def test_real_use_case():
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
