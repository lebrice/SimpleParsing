
from dataclasses import dataclass, field
from typing import *
from . import TestSetup

__all__ = [
    "HParams",
    "RunConfig",
    "TrainConfig",
    "TaskModelParams",
    "HyperParameters",
]

@dataclass
class HParams(TestSetup):
    """
    Model Hyper-parameters
    """
    # Number of examples per batch
    batch_size: int = 32
    # fixed learning rate passed to the optimizer.
    learning_rate: float = 0.005 
    # name of the optimizer class to use
    optimizer: str = "ADAM"
    
    
    default_num_layers: ClassVar[int] = 10
    
    # number of layers.
    num_layers: int = default_num_layers
    # the number of neurons at each layer
    neurons_per_layer: List[int] = field(default_factory=lambda: [128] * HParams.default_num_layers)


@dataclass
class RunConfig(TestSetup):
    """
    Group of settings used during a training or validation run.
    """
    # the set of hyperparameters for this run.
    hparams: HParams = HParams()
    log_dir: str = "logs" # The logging directory where
    checkpoint_dir: str = field(init=False)
    
    def __post_init__(self):
        """Post-Init to set the fields that shouldn't be constructor arguments."""
        import os
        self.checkpoint_dir = os.path.join(self.log_dir, "checkpoints")


@dataclass
class TrainConfig(TestSetup):
    """
    Top-level settings for multiple runs.
    """
    # run config to be used during training
    train: RunConfig = RunConfig(log_dir="train")
    # run config to be used during validation.
    valid: RunConfig = RunConfig(log_dir="valid")

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
    gender: TaskModelParams = field(default_factory=lambda: TaskModelParams(num_layers=1, num_units=32, use_likes=False))

    # Age Group Model settings:
    age_group: TaskModelParams = field(default_factory=lambda: TaskModelParams(num_layers=2, num_units=64, use_likes=True, likes_condensing_layers=1, likes_condensing_units=16))
    
    # Personality Model(s) settings:
    personality: TaskModelParams = field(default_factory=lambda: TaskModelParams(num_layers=1, num_units=8, use_likes=False))
