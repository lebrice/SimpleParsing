import argparse
import dataclasses
import shlex
from dataclasses import dataclass, field
from typing import *

import pytest

from .testutils import TestSetup
from simple_parsing import *

@dataclass()
class ClassA():
    a: int = 1


@dataclass()
class ClassB():
    b: int = 2


@dataclass()
class ClassC():
    c: int = 3


@dataclass()
class Container1(TestSetup):
    v1: int = 0
    class_a: ClassA = ClassA()
    class_b: ClassB = ClassB()

@dataclass()
class Container2(TestSetup):
    v2: int = 0
    class_a: ClassA = ClassA()
    class_b: ClassB = ClassB()

@dataclass()
class ContainerWithList(TestSetup):
    list_of_class_c: List[ClassC] = field(default_factory=lambda: [ClassC()] * 2)


xfail_nesting_with_containers_isnt_supported_yet = pytest.mark.xfail(reason="TODO: make sure this is how people would want to use this feature.")

def test_nesting_no_args():
    c1 = Container1.setup("")
    assert c1.v1 == 0
    assert c1.class_a.a == 1
    assert c1.class_b.b == 2

def test_nesting_with_args():
    c1 = Container1.setup("--a 123 --b 456 --v1 3")
    assert c1.v1 == 3
    assert c1.class_a.a == 123
    assert c1.class_b.b == 456


@xfail_nesting_with_containers_isnt_supported_yet
def test_nesting_with_containers_no_args():
    container = ContainerWithList.setup("")
    assert len(container.list_of_class_c) == 2


@xfail_nesting_with_containers_isnt_supported_yet
def test_nesting_with_containers_with_args():
    container = ContainerWithList.setup("--c 1 2")
    assert len(container.list_of_class_c) == 2
    c1, c2 = tuple(container.list_of_class_c)
    assert c1.c == 1
    assert isinstance(c1, ClassC)
    assert c2.c == 2
    assert isinstance(c2, ClassC)


@xfail_nesting_with_containers_isnt_supported_yet
def test_nesting_multiple_containers_with_args_separator():
    container1, container2, container3 = ContainerWithList.setup_multiple(3, "--c 1 2 --c 3 4 --c 5 6")
    assert len(container1.list_of_class_c) == 2
    c1, c2 = tuple(container1.list_of_class_c)
    assert c1.c == 1
    assert isinstance(c1, ClassC)
    assert c2.c == 2
    assert isinstance(c2, ClassC)


    assert len(container2.list_of_class_c) == 2
    c1, c2 = tuple(container2.list_of_class_c)
    assert c1.c == 3
    assert isinstance(c1, ClassC)
    assert c2.c == 4
    assert isinstance(c2, ClassC)

    assert len(container3.list_of_class_c) == 2
    c1, c2 = tuple(container3.list_of_class_c)
    assert c1.c == 5
    assert isinstance(c1, ClassC)
    assert c2.c == 6
    assert isinstance(c2, ClassC)

@dataclass
class HParams:
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
class RunConfig:
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


def test_train_config_example_no_args():
    config = TrainConfig.setup("", conflict_resolution_mode=ConflictResolution.ALWAYS_MERGE)
    assert isinstance(config.train, RunConfig)
    import os
    assert config.train.checkpoint_dir == os.path.join("logs","checkpoints")
    
    assert isinstance(config.valid, RunConfig)
    assert config.valid.checkpoint_dir == os.path.join("logs","checkpoints")
    
    print(TrainConfig.get_help_text())

def test_train_config_example_with_explicit_args():
    config = TrainConfig.setup(
        "--train.log_dir train "
        "--train.hparams.batch_size 123 "
        "--valid.log_dir valid "
        "--valid.hparams.batch_size 456",
        conflict_resolution_mode=ConflictResolution.EXPLICIT
    )
    import os
    
    assert isinstance(config.train, RunConfig)
    assert config.train.checkpoint_dir == os.path.join("train","checkpoints")
    
    assert isinstance(config.train.hparams, HParams)
    assert config.train.hparams.batch_size == 123

    assert isinstance(config.valid, RunConfig)
    assert config.valid.checkpoint_dir == os.path.join("valid","checkpoints")
    
    assert isinstance(config.valid.hparams, HParams)
    assert config.valid.hparams.batch_size == 456

    print(TrainConfig.get_help_text())
