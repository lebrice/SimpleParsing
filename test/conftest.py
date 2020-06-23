import logging
import shlex
from dataclasses import dataclass, field
from typing import *

import pytest

from simple_parsing import choice
from simple_parsing.helpers import Serializable

from .testutils import TestSetup

# List of simple attributes to use in test:
simple_arguments: List[Tuple[Type, Any, Any]] = [
    # type, passed value, expected (parsed) value
    (int,   "123",  123),
    (int,   123,    123),
    (int,   "-1",     -1),

    (float, "123.0",  123.0),
    (float, "'0.0'",  0.0),
    (float, "0.123",  0.123),
    (float, "0.123",  0.123),
    (float, 0.123,  0.123),
    (float, 123,  123.0),

    (bool, "True",  True),
    (bool, "False",  False),
    (bool, "true",  True),
    (bool, "false",  False),
    (bool, "yes",  True),
    (bool, "no",  False),
    (bool, "T",  True),
    (bool, "F",  False),

    (str, "bob", "bob"),
    (str, "'bob'", "bob"),
    (str, "''", ""),
    (str, "[123]", "[123]"),
    (str, "123", "123"),
]


@pytest.fixture(params=simple_arguments)
def simple_attribute(request):
    """ Test fixture that produces an tuple of (type, passed value, expected value) """
    some_type, passed_value, expected_value = request.param
    logging.debug(f"Attribute type: {some_type}, passed value: '{passed_value}', expected: '{expected_value}'")
    return request.param


@pytest.fixture(scope="module")
def parser():
    from .testutils import TestParser
    _parser = TestParser()
    return _parser


@pytest.fixture
def no_stdout(capsys, caplog):
    """Asserts that no output was produced on stdout.
    
    Args:
        capsys (pytest.fixture): The capsys fixture
    """
    with caplog.at_level(logging.DEBUG):
        yield
    captured = capsys.readouterr()
    if captured.out != "":
        pytest.fail(f"Test generated some output in stdout: '{captured.out}'")
    if captured.err != "":
        pytest.fail(f"Test generated some output in stderr: '{captured.err}'")

@pytest.fixture
def no_warnings(caplog):
    yield
    for when in ("setup", "call"):
        messages = [
            x.message for x in caplog.get_records(when) if x.levelno == logging.WARNING
        ]
        if messages:
            pytest.fail(
                "warning messages encountered during testing: {}".format(messages)
            )

@pytest.fixture
def silent(no_stdout, no_warnings):
    """
    Test fixture that will make a test fail if it prints anything to stdout or 
    logs warnings
    """
    pass



@pytest.fixture
def TaskHyperParameters():
    """ Test fixture that gives a good example use-case from a real datascience
    project.
    """
    @dataclass
    class TaskHyperParameters(TestSetup, Serializable):
        """
        HyperParameters for a task-specific model
        """
        name: str                       # name of the task
        num_layers: int = 1             # number of dense layers
        num_units: int = 8              # units per layer
        activation: str = choice("tanh", "relu", "linear", default="tanh") # activation function
        use_batchnorm: bool = False     # wether or not to use batch normalization after each dense layer
        use_dropout: bool = True        # wether or not to use dropout after each dense layer
        dropout_rate: float = 0.1       # the dropout rate
        use_image_features: bool = True # wether or not image features should be used as input
        use_likes: bool = True          # wether or not 'likes' features should be used as input
        l1_reg: float = 0.005           # L1 regularization coefficient
        l2_reg: float = 0.005           # L2 regularization coefficient

        # Wether or not a task-specific Embedding layer should be used on the 'likes' features.
        # When set to 'True', it is expected that there no shared embedding is used.
        embed_likes: bool = False
    return TaskHyperParameters


@pytest.fixture
def HyperParameters(TaskHyperParameters):  
    @dataclass
    class HyperParameters(TestSetup, Serializable):
        """Hyperparameters of a multi-headed model."""
        
        batch_size: int = 128           # the batch size
        learning_rate: float = 0.001    # Learning Rate
        optimizer: str = choice("SGD", "ADAM", default="SGD")   # Which optimizer to use during training.

        # number of individual 'pages' that were kept during preprocessing of the 'likes'.
        # This corresponds to the number of entries in the multi-hot like vector.
        num_like_pages: int = 10_000

        gender_loss_weight: float   = 1.0   # relative weight of the gender loss
        age_loss_weight: float      = 1.0   # relative weight of the age_group loss

        num_text_features: ClassVar[int] = 91   
        num_image_features: ClassVar[int] = 65

        max_number_of_likes: int = 2000
        embedding_dim: int = 8

        shared_likes_embedding: bool = True

        # Wether or not to better filtering of liked pages
        use_custom_likes: bool = True

        # Gender model settings
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

        # Age Group Model settings
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
    return HyperParameters
