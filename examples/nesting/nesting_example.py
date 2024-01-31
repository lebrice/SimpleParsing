import functools
from dataclasses import dataclass, field
from typing import ClassVar

from simple_parsing import ArgumentParser


@dataclass
class TaskHyperParameters:
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
class HyperParameters:
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


parser = ArgumentParser()
parser.add_arguments(HyperParameters, dest="hparams")
args = parser.parse_args()
hparams: HyperParameters = args.hparams
print(hparams)
expected = (
    "HyperParameters(batch_size=128, optimizer='sgd', "
    "learning_rate=0.001, num_like_pages=10000, gender_loss_weight=1.0, "
    "age_loss_weight=1.0, max_number_of_likes=2000, embedding_dim=8, "
    "shared_likes_embedding=True, use_custom_likes=True, "
    "gender=TaskHyperParameters(name='gender', num_layers=1, num_units=32, "
    "activation='tanh', use_batchnorm=False, use_dropout=True, dropout_rate=0.1, "
    "use_image_features=True, use_likes=True, l1_reg=0.005, l2_reg=0.005, "
    "embed_likes=False), age_group=TaskHyperParameters(name='age_group', "
    "num_layers=2, num_units=64, activation='tanh', use_batchnorm=False, "
    "use_dropout=True, dropout_rate=0.1, use_image_features=True, use_likes=True, "
    "l1_reg=0.005, l2_reg=0.005, embed_likes=False), "
    "personality=TaskHyperParameters(name='personality', num_layers=1, num_units=8, "
    "activation='tanh', use_batchnorm=False, use_dropout=True, dropout_rate=0.1, "
    "use_image_features=False, use_likes=False, l1_reg=0.005, l2_reg=0.005, "
    "embed_likes=False))"
)
