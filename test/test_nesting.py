import argparse
import dataclasses
import shlex
from dataclasses import dataclass, field
from typing import *

import pytest

from .testutils import TestSetup
from simple_parsing import (Formatter, InconsistentArgumentError,
                            ArgumentParser)

    
# call a test function multiple times passing in different arguments in turn.
# argvalues generally needs to be a list of values if argnames specifies only one name or a list of tuples of values if argnames specifies multiple names.
# Example: @parametrize('arg1', [1,2]) would lead to two calls of the decorated test function,
# one with arg1=1 and another with arg1=2.see https://docs.pytest.org/en/latest/parametrize.html for more info and examples.


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
class ContainerWithList(TestSetup):
    list_of_class_c: List[ClassC] = field(default_factory=lambda: [ClassC()] * 2)


xfail_nesting_isnt_supported_yet = pytest.mark.xfail(reason="TODO: make sure this is how people would want to use this feature.")

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


def test_nesting_with_containers_no_args():
    container = ContainerWithList.setup("")
    assert len(container.list_of_class_c) == 2


def test_nesting_with_containers_with_args():
    container = ContainerWithList.setup("--c 1 2")
    assert len(container.list_of_class_c) == 2
    c1, c2 = tuple(container.list_of_class_c)
    assert c1.c == 1
    assert isinstance(c1, ClassC)
    assert c2.c == 2
    assert isinstance(c2, ClassC)


@xfail_nesting_isnt_supported_yet
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
class RunConfig:
    log_dir: str = "logs"
    checkpoint_dir: str = field(init=False)
    
    def __post_init__(self):
        """Post-Init to set the fields that shouldn't be constructor arguments."""
        import os
        self.checkpoint_dir = os.path.join(self.log_dir, "checkpoints")

@dataclass
class TrainConfig(TestSetup):
    train_config: RunConfig = RunConfig("train")
    valid_config: RunConfig = RunConfig("valid")

def test_train_config_example_no_args():
    config = TrainConfig.setup("")
    assert isinstance(config.train_config, RunConfig)
    assert config.train_config.checkpoint_dir == "logs/checkpoints"
    
    assert isinstance(config.valid_config, RunConfig)
    assert config.valid_config.checkpoint_dir == "logs/checkpoints"
    
    print(TrainConfig.get_help_text())

