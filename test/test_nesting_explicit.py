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
    num_layers: int = 1
    num_units: int = 32
    use_batchnorm: bool = False
    use_dropout: bool = False
    dropout_rate: float = 0.1
    use_likes: bool = False
    likes_condensing_layers: int = 0
    likes_condensing_units: int = 0


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
    gender: TaskModelParams = TaskModelParams(num_layers=1, num_units=32, use_likes=False)

    # Age Group Model settings:
    age_group: TaskModelParams = TaskModelParams(num_layers=2, num_units=64, use_likes=True, likes_condensing_layers=1, likes_condensing_units=16)
    
    # Personality Model(s) settings:
    personality: TaskModelParams = TaskModelParams(num_layers=1, num_units=8, use_likes=False)
    

def test_real_use_case():
    hparams = HyperParameters.setup("--help --age_group.use_likes False", conflict_resolution_mode=ConflictResolution.EXPLICIT)
    assert isinstance(hparams, HyperParameters)
    print(hparams.get_help_text())
    assert hasattr(hparams, "age_group")
    assert isinstance(hparams.age_group, TaskModelParams)
    assert isinstance(hparams.age_group.use_likes, bool)
    assert hparams.age_group.use_likes == False
