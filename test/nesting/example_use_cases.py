import functools
from dataclasses import dataclass, field
from typing import ClassVar

from simple_parsing.helpers.serialization.serializable import Serializable

from ..test_utils import TestSetup

__all__ = [
    "HParams",
    "RunConfig",
    "TrainConfig",
    "TaskHyperParameters",
    "HyperParameters",
]


@dataclass
class HParams(TestSetup):
    """Model Hyper-parameters."""

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
    neurons_per_layer: list[int] = field(
        default_factory=lambda: [128] * HParams.default_num_layers
    )


@dataclass
class RunConfig(TestSetup):
    """Group of settings used during a training or validation run."""

    # the set of hyperparameters for this run.
    hparams: HParams = field(default_factory=HParams)
    log_dir: str = "logs"  # The logging directory where
    checkpoint_dir: str = field(init=False)

    def __post_init__(self):
        """Post-Init to set the fields that shouldn't be constructor arguments."""
        import os

        self.checkpoint_dir = os.path.join(self.log_dir, "checkpoints")


@dataclass
class TrainConfig(TestSetup):
    """Top-level settings for multiple runs."""

    # run config to be used during training
    train: RunConfig = field(default_factory=functools.partial(RunConfig, log_dir="train"))
    # run config to be used during validation.
    valid: RunConfig = field(default_factory=functools.partial(RunConfig, log_dir="valid"))


@dataclass
class TaskHyperParameters(TestSetup):
    """HyperParameters for a task-specific model."""

    # name of the task
    name: str
    # number of dense layers
    num_layers: int = 1
    # units per layer
    num_units: int = 8
    # activation function
    activation: str = "tanh"
    # whether or not to use batch normalization after each dense layer
    use_batchnorm: bool = False
    # whether or not to use dropout after each dense layer
    use_dropout: bool = True
    # the dropout rate
    dropout_rate: float = 0.1
    # whether or not image features should be used as input
    use_image_features: bool = True
    # whether or not 'likes' features should be used as input
    use_likes: bool = True
    # L1 regularization coefficient
    l1_reg: float = 0.005
    # L2 regularization coefficient
    l2_reg: float = 0.005
    # Whether or not a task-specific Embedding layer should be used on the 'likes' features.
    # When set to 'True', it is expected that there no shared embedding is used.
    embed_likes: bool = False


@dataclass
class HyperParameters(TestSetup, Serializable):
    """Hyperparameters of our model."""

    # the batch size
    batch_size: int = 128
    # Which optimizer to use during training.
    optimizer: str = "sgd"
    # Learning Rate
    learning_rate: float = 0.001

    # number of individual 'pages' that were kept during preprocessing of the 'likes'.
    # This corresponds to the number of entries in the multi-hot like vector.
    num_like_pages: int = 10_000

    gender_loss_weight: float = 1.0
    age_loss_weight: float = 1.0

    num_text_features: ClassVar[int] = 91
    num_image_features: ClassVar[int] = 65

    max_number_of_likes: int = 2000
    embedding_dim: int = 8

    shared_likes_embedding: bool = True

    # Whether or not to use Rémi's better kept like pages
    use_custom_likes: bool = True

    # Gender model settings:
    gender: TaskHyperParameters = field(
        default_factory=functools.partial(
            TaskHyperParameters,
            "gender",
            num_layers=1,
            num_units=32,
            use_batchnorm=False,
            use_dropout=True,
            dropout_rate=0.1,
            use_image_features=True,
            use_likes=True,
        )
    )

    # Age Group Model settings:
    age_group: TaskHyperParameters = field(
        default_factory=functools.partial(
            TaskHyperParameters,
            "age_group",
            num_layers=2,
            num_units=64,
            use_batchnorm=False,
            use_dropout=True,
            dropout_rate=0.1,
            use_image_features=True,
            use_likes=True,
        )
    )

    # Personality Model(s) settings:
    personality: TaskHyperParameters = field(
        default_factory=functools.partial(
            TaskHyperParameters,
            "personality",
            num_layers=1,
            num_units=8,
            use_batchnorm=False,
            use_dropout=True,
            dropout_rate=0.1,
            use_image_features=False,
            use_likes=False,
        )
    )
