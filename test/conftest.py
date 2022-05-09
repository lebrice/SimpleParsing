import logging
import sys
from dataclasses import dataclass
from typing import Any, ClassVar, List, Optional, Tuple, Type

import pytest

pytest.register_assert_rewrite("test.testutils")


from simple_parsing import choice
from simple_parsing.helpers import Serializable

collect_ignore = []
if sys.version_info < (3, 7):
    collect_ignore.append("test_future_annotations.py")


# List of simple attributes to use in test:
simple_arguments: List[Tuple[Type, Any, Any]] = [
    # type, passed value, expected (parsed) value
    (int, "123", 123),
    (int, 123, 123),
    (int, "-1", -1),
    (float, "123.0", 123.0),
    (float, "'0.0'", 0.0),
    (float, "0.123", 0.123),
    (float, "0.123", 0.123),
    (float, 0.123, 0.123),
    (float, 123, 123.0),
    (bool, "True", True),
    (bool, "False", False),
    (bool, "true", True),
    (bool, "false", False),
    (bool, "yes", True),
    (bool, "no", False),
    (bool, "T", True),
    (bool, "F", False),
    (str, "bob", "bob"),
    (str, "'bob'", "bob"),
    (str, "''", ""),
    (str, "[123]", "[123]"),
    (str, "123", "123"),
]


@pytest.fixture(params=simple_arguments)
def simple_attribute(request):
    """Test fixture that produces an tuple of (type, passed value, expected value)"""
    some_type, passed_value, expected_value = request.param
    logging.debug(
        f"Attribute type: {some_type}, passed value: '{passed_value}', expected: '{expected_value}'"
    )
    return request.param


@pytest.fixture
def assert_equals_stdout(capsys):
    def strip(string):
        return "".join(string.split())

    def should_equal(expected: str, file_path: Optional[str] = None):
        if "optional arguments" in expected and sys.version_info >= (3, 10):
            expected = expected.replace("optional arguments", "options")
        out = capsys.readouterr().out
        assert strip(out) == strip(expected), file_path

    return should_equal


from logging import getLogger as get_logger


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    project_logger = get_logger("simple_parsing")
    project_logger.setLevel(
        logging.DEBUG
        if "-vv" in sys.argv
        else logging.INFO
        if "-v" in sys.argv
        else logging.WARNING
    )
    ch = logging.StreamHandler(stream=sys.stdout)
    ch.setFormatter(
        logging.Formatter(
            "[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s",
            "%m-%d %H:%M:%S"
            # "%(asctime)-15s::%(levelname)s::%(pathname)s::%(lineno)d::%(message)s"
        )
    )
    project_logger.addHandler(ch)


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
        messages = [x.message for x in caplog.get_records(when) if x.levelno == logging.WARNING]
        if messages:
            pytest.fail(f"warning messages encountered during testing: {messages}")


@pytest.fixture
def silent(no_stdout, no_warnings):
    """
    Test fixture that will make a test fail if it prints anything to stdout or
    logs warnings
    """


@pytest.fixture
def logs_warning(caplog):
    yield
    messages = [x.message for x in caplog.get_records("call") if x.levelno == logging.WARNING]
    if not messages:
        pytest.fail(f"No warning messages were logged: {messages}")


@pytest.fixture
def TaskHyperParameters():
    """Test fixture that gives a good example use-case from a real datascience
    project.
    """
    from .testutils import TestSetup

    @dataclass
    class TaskHyperParameters(TestSetup, Serializable):
        """
        HyperParameters for a task-specific model
        """

        name: str  # name of the task
        num_layers: int = 1  # number of dense layers
        num_units: int = 8  # units per layer
        activation: str = choice("tanh", "relu", "linear", default="tanh")  # activation function
        use_batchnorm: bool = (
            False  # whether or not to use batch normalization after each dense layer
        )
        use_dropout: bool = True  # whether or not to use dropout after each dense layer
        dropout_rate: float = 0.1  # the dropout rate
        use_image_features: bool = True  # whether or not image features should be used as input
        use_likes: bool = True  # whether or not 'likes' features should be used as input
        l1_reg: float = 0.005  # L1 regularization coefficient
        l2_reg: float = 0.005  # L2 regularization coefficient

        # Whether or not a task-specific Embedding layer should be used on the 'likes' features.
        # When set to 'True', it is expected that there no shared embedding is used.
        embed_likes: bool = False

    return TaskHyperParameters


@pytest.fixture
def HyperParameters(TaskHyperParameters):
    from .testutils import TestSetup

    @dataclass
    class HyperParameters(TestSetup, Serializable):
        """Hyperparameters of a multi-headed model."""

        batch_size: int = 128  # the batch size
        learning_rate: float = 0.001  # Learning Rate
        optimizer: str = choice(
            "SGD", "ADAM", default="SGD"
        )  # Which optimizer to use during training.

        # number of individual 'pages' that were kept during preprocessing of the 'likes'.
        # This corresponds to the number of entries in the multi-hot like vector.
        num_like_pages: int = 10_000

        gender_loss_weight: float = 1.0  # relative weight of the gender loss
        age_loss_weight: float = 1.0  # relative weight of the age_group loss

        num_text_features: ClassVar[int] = 91
        num_image_features: ClassVar[int] = 65

        max_number_of_likes: int = 2000
        embedding_dim: int = 8

        shared_likes_embedding: bool = True

        # Whether or not to better filtering of liked pages
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
