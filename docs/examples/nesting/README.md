# Nesting!!

You can nest dataclasses within dataclasses. In the following example (taken from an actual Data Science project), we show how we can reuse the `TaskHyperParameters` class to define the parameters of three models: `gender`, `age_group`, and `personality`:

```python
from simple_parsing import ArgumentParser
from dataclasses import dataclass
from typing import *

@dataclass
class TaskHyperParameters():
    """
    HyperParameters for a task-specific model
    """
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
class HyperParameters():
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

    gender_loss_weight: float   = 1.0
    age_loss_weight: float      = 1.0

    num_text_features: ClassVar[int] = 91
    num_image_features: ClassVar[int] = 65

    max_number_of_likes: int = 2000
    embedding_dim: int = 8

    shared_likes_embedding: bool = True

    # Whether or not to use Rémi's better kept like pages
    use_custom_likes: bool = True

    # Gender model settings:
    gender: TaskHyperParameters = TaskHyperParameters(
        "gender",
        num_layers=1,
        num_units=32,
        use_batchnorm=False,
        use_dropout=True,
        dropout_rate=0.1,
        use_image_features=True,
        use_likes=True,
    )

    # Age Group Model settings:
    age_group: TaskHyperParameters = TaskHyperParameters(
        "age_group",
        num_layers=2,
        num_units=64,
        use_batchnorm=False,
        use_dropout=True,
        dropout_rate=0.1,
        use_image_features=True,
        use_likes=True,
    )

    # Personality Model(s) settings:
    personality: TaskHyperParameters = TaskHyperParameters(
        "personality",
        num_layers=1,
        num_units=8,
        use_batchnorm=False,
        use_dropout=True,
        dropout_rate=0.1,
        use_image_features=False,
        use_likes=False,
    )


parser = ArgumentParser()
parser.add_arguments(HyperParameters, dest="hparams")
args = parser.parse_args()
hparams: HyperParameters = args.hparams
print(hparams)
```

The help string we get would have been impossibly hard to create by hand:

```console
$ python nesting_example.py --help
usage: nesting_example.py [-h] [--batch_size int] [--optimizer str]
                          [--learning_rate float] [--num_like_pages int]
                          [--gender_loss_weight float]
                          [--age_loss_weight float]
                          [--max_number_of_likes int] [--embedding_dim int]
                          [--shared_likes_embedding [bool]]
                          [--use_custom_likes [bool]] [--gender.name str]
                          [--gender.num_layers int] [--gender.num_units int]
                          [--gender.activation str]
                          [--gender.use_batchnorm [bool]]
                          [--gender.use_dropout [bool]]
                          [--gender.dropout_rate float]
                          [--gender.use_image_features [bool]]
                          [--gender.use_likes [bool]]
                          [--gender.l1_reg float] [--gender.l2_reg float]
                          [--gender.embed_likes [bool]]
                          [--age_group.name str] [--age_group.num_layers int]
                          [--age_group.num_units int]
                          [--age_group.activation str]
                          [--age_group.use_batchnorm [bool]]
                          [--age_group.use_dropout [bool]]
                          [--age_group.dropout_rate float]
                          [--age_group.use_image_features [bool]]
                          [--age_group.use_likes [bool]]
                          [--age_group.l1_reg float]
                          [--age_group.l2_reg float]
                          [--age_group.embed_likes [bool]]
                          [--personality.name str]
                          [--personality.num_layers int]
                          [--personality.num_units int]
                          [--personality.activation str]
                          [--personality.use_batchnorm [bool]]
                          [--personality.use_dropout [bool]]
                          [--personality.dropout_rate float]
                          [--personality.use_image_features [bool]]
                          [--personality.use_likes [bool]]
                          [--personality.l1_reg float]
                          [--personality.l2_reg float]
                          [--personality.embed_likes [bool]]

optional arguments:
  -h, --help            show this help message and exit

HyperParameters ['hparams']:
  Hyperparameters of our model.

  --batch_size int      the batch size (default: 128)
  --optimizer str       Which optimizer to use during training. (default: sgd)
  --learning_rate float
                        Learning Rate (default: 0.001)
  --num_like_pages int  number of individual 'pages' that were kept during
                        preprocessing of the 'likes'. This corresponds to the
                        number of entries in the multi-hot like vector.
                        (default: 10000)
  --gender_loss_weight float
  --age_loss_weight float
  --max_number_of_likes int
  --embedding_dim int
  --shared_likes_embedding [bool]
  --use_custom_likes [bool]
                        Whether or not to use Rémi's better kept like pages
                        (default: True)

TaskHyperParameters ['hparams.gender']:
  Gender model settings:

  --gender.name str     name of the task (default: gender)
  --gender.num_layers int
                        number of dense layers (default: 1)
  --gender.num_units int
                        units per layer (default: 32)
  --gender.activation str
                        activation function (default: tanh)
  --gender.use_batchnorm [bool]
                        whether or not to use batch normalization after each
                        dense layer (default: False)
  --gender.use_dropout [bool]
                        whether or not to use dropout after each dense layer
                        (default: True)
  --gender.dropout_rate float
                        the dropout rate (default: 0.1)
  --gender.use_image_features [bool]
                        whether or not image features should be used as input
                        (default: True)
  --gender.use_likes [bool]
                        whether or not 'likes' features should be used as input
                        (default: True)
  --gender.l1_reg float
                        L1 regularization coefficient (default: 0.005)
  --gender.l2_reg float
                        L2 regularization coefficient (default: 0.005)
  --gender.embed_likes [bool]
                        Whether or not a task-specific Embedding layer should
                        be used on the 'likes' features. When set to 'True',
                        it is expected that there no shared embedding is used.
                        (default: False)

TaskHyperParameters ['hparams.age_group']:
  Age Group Model settings:

  --age_group.name str  name of the task (default: age_group)
  --age_group.num_layers int
                        number of dense layers (default: 2)
  --age_group.num_units int
                        units per layer (default: 64)
  --age_group.activation str
                        activation function (default: tanh)
  --age_group.use_batchnorm [bool]
                        whether or not to use batch normalization after each
                        dense layer (default: False)
  --age_group.use_dropout [bool]
                        whether or not to use dropout after each dense layer
                        (default: True)
  --age_group.dropout_rate float
                        the dropout rate (default: 0.1)
  --age_group.use_image_features [bool]
                        whether or not image features should be used as input
                        (default: True)
  --age_group.use_likes [bool]
                        whether or not 'likes' features should be used as input
                        (default: True)
  --age_group.l1_reg float
                        L1 regularization coefficient (default: 0.005)
  --age_group.l2_reg float
                        L2 regularization coefficient (default: 0.005)
  --age_group.embed_likes [bool]
                        Whether or not a task-specific Embedding layer should
                        be used on the 'likes' features. When set to 'True',
                        it is expected that there no shared embedding is used.
                        (default: False)

TaskHyperParameters ['hparams.personality']:
  Personality Model(s) settings:

  --personality.name str
                        name of the task (default: personality)
  --personality.num_layers int
                        number of dense layers (default: 1)
  --personality.num_units int
                        units per layer (default: 8)
  --personality.activation str
                        activation function (default: tanh)
  --personality.use_batchnorm [bool]
                        whether or not to use batch normalization after each
                        dense layer (default: False)
  --personality.use_dropout [bool]
                        whether or not to use dropout after each dense layer
                        (default: True)
  --personality.dropout_rate float
                        the dropout rate (default: 0.1)
  --personality.use_image_features [bool]
                        whether or not image features should be used as input
                        (default: False)
  --personality.use_likes [bool]
                        whether or not 'likes' features should be used as input
                        (default: False)
  --personality.l1_reg float
                        L1 regularization coefficient (default: 0.005)
  --personality.l2_reg float
                        L2 regularization coefficient (default: 0.005)
  --personality.embed_likes [bool]
                        Whether or not a task-specific Embedding layer should
                        be used on the 'likes' features. When set to 'True',
                        it is expected that there no shared embedding is used.
                        (default: False)
```
