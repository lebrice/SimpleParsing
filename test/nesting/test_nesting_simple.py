from dataclasses import dataclass
from typing import Optional

import pytest

import simple_parsing
from simple_parsing import ConflictResolution, field

from ..testutils import TestSetup
from .example_use_cases import HParams, RunConfig, TrainConfig


@dataclass
class ClassA:
    a: int = 1


@dataclass
class ClassB:
    b: int = 2


@dataclass
class ClassC:
    c: int = 3


@dataclass
class Container1(TestSetup):
    v1: int = 0
    class_a: ClassA = field(default_factory=ClassA)
    class_b: ClassB = field(default_factory=ClassB)


@dataclass
class Container2(TestSetup):
    v2: int = 0
    class_a: ClassA = field(default_factory=ClassA)
    class_b: ClassB = field(default_factory=ClassB)


@dataclass
class ContainerWithList(TestSetup):
    list_of_class_c: list[ClassC] = field(default_factory=lambda: [ClassC()] * 2)


xfail_nesting_with_containers_isnt_supported_yet = pytest.mark.xfail(
    reason="TODO: make sure this is how people would want to use this feature."
)


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
    container1, container2, container3 = ContainerWithList.setup_multiple(
        3, "--c 1 2 --c 3 4 --c 5 6"
    )
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


def test_train_config_example_no_args():
    config = TrainConfig.setup("", conflict_resolution_mode=ConflictResolution.ALWAYS_MERGE)
    assert isinstance(config.train, RunConfig)
    import os

    assert config.train.checkpoint_dir == os.path.join("train", "checkpoints")

    assert isinstance(config.valid, RunConfig)
    assert config.valid.checkpoint_dir == os.path.join("valid", "checkpoints")

    print(TrainConfig.get_help_text())


def test_train_config_example_with_explicit_args():
    config = TrainConfig.setup(
        "--train_config.train.log_dir train "
        "--train_config.train.hparams.batch_size 123 "
        "--train_config.valid.log_dir valid "
        "--train_config.valid.hparams.batch_size 456",
        conflict_resolution_mode=ConflictResolution.EXPLICIT,
    )
    import os

    assert isinstance(config.train, RunConfig)
    assert config.train.checkpoint_dir == os.path.join("train", "checkpoints")

    assert isinstance(config.train.hparams, HParams)
    assert config.train.hparams.batch_size == 123

    assert isinstance(config.valid, RunConfig)
    assert config.valid.checkpoint_dir == os.path.join("valid", "checkpoints")

    assert isinstance(config.valid.hparams, HParams)
    assert config.valid.hparams.batch_size == 456

    print(TrainConfig.get_help_text())


def test_nesting_defaults():
    @dataclass
    class A(TestSetup):
        p: int
        q: float

    @dataclass
    class B(TestSetup):
        x: int
        y: A

    parser = simple_parsing.ArgumentParser()
    default = B(x=3, y=A(p=4, q=0.1))
    parser.add_arguments(B, dest="b", default=default)
    assert parser.parse_args("").b == default


def test_nesting_defaults_with_optional():
    @dataclass
    class A(TestSetup):
        p: int
        q: float

    @dataclass
    class B(TestSetup):
        x: int
        y: Optional[A] = None  # NOTE: The Optional annotation is causing trouble here.

    # This is because of the code that we have to check for optional parameter groups. If we don't
    # detect any arguments from the group of the type `A`, then we just use None, because the field
    # is marked as Optional. However, we should instead use the default value that is provided as
    # an argument to `add_arguments`.
    parser = simple_parsing.ArgumentParser()
    default = B(x=3, y=A(p=4, q=0.1))
    parser.add_arguments(B, dest="b", default=default)
    assert parser.parse_args("").b == default
