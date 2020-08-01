from typing import Container
import argparse
import dataclasses
import shlex
from dataclasses import dataclass, field
from typing import *

import pytest

from simple_parsing import (InconsistentArgumentError,
                            ArgumentParser)

from .testutils import *


def test_multiple_at_same_dest_throws_error():
    @dataclass
    class SomeClass:
        a: int = 123

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, "some_class")
    with raises(argparse.ArgumentError):
        parser.add_arguments(SomeClass, "some_class")


@xfail(reason="Not sure if this syntax should also be allowed...")
def test_multiple_append_syntax():
    @dataclass
    class SomeClass(TestSetup):
        a: int = 123

    c1, c2, c3 = SomeClass.setup_multiple(3, arguments="--a 1 --a 2 --a 3")
    assert c1.a == 1
    assert c2.a == 2
    assert c3.a == 3


@parametrize("num_instances", [1, 2, 5])
def test_parse_multiple_with_no_arguments_sets_default_value(num_instances: int, simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass(TestSetup):
        a: some_type = expected_value  # type: ignore
        """some docstring for attribute 'a'"""

    classes = SomeClass.setup_multiple(num_instances, "")
    assert len(classes) == num_instances
    for i in range(num_instances):
        c_i = classes[i]
        assert isinstance(c_i, SomeClass)
        assert c_i.a == expected_value
        assert isinstance(c_i.a, some_type)


@parametrize("num_instances", [1, 2, 5])
def test_parse_multiple_with_single_arg_value_sets_that_value_for_all_instances(
    num_instances: int,
    simple_attribute,
    silent,
):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass(TestSetup):
        a: some_type = expected_value  # type: ignore
        """some docstring for attribute 'a'"""
    classes = SomeClass.setup_multiple(num_instances, f"--a {passed_value}")

    assert len(classes) == num_instances
    for i in range(num_instances):
        c_i = classes[i]
        assert isinstance(c_i, SomeClass)
        assert c_i.a == expected_value
        assert isinstance(c_i.a, some_type)


@parametrize(
    "some_type, default_value,  passed_values",
    [
        (int,   123524,     [1, 2, 3]),
        (float, 123.456,    [4.5, -12.3, 9]),
        (str,   "bob",      ["random", "triceratops", "cocobongo"]),
        (bool,  True,       [False, True, False]),
    ])
def test_parse_multiple_with_provided_value_for_each_instance(
    some_type: Type,
    default_value: Any,
    passed_values: List[Any],
    silent
):

    @dataclass
    class SomeClass(TestSetup):
        a: some_type = default_value  # type: ignore
        """some docstring for attribute 'a'"""
    # TODO: maybe test out other syntaxes for passing in multiple argument values? (This looks a lot like passing in a list of values..)
    arguments = f"--a {' '.join(str(p) for p in passed_values)}"
    classes = SomeClass.setup_multiple(3, arguments)

    assert len(classes) == 3
    for i in range(3):
        c_i = classes[i]
        assert isinstance(c_i, SomeClass)
        assert c_i.a == passed_values[i]
        assert isinstance(c_i.a, some_type)


@parametrize("some_type", [int, float, str, bool])
def test_parse_multiple_without_required_arguments(some_type: Type):
    @dataclass
    class SomeClass(TestSetup):
        a: some_type  # type: ignore
        """some docstring for attribute 'a'"""

    with raises():
        some_class = SomeClass.setup_multiple(2, "")


@parametrize("container_type", [List, Tuple])
@parametrize("item_type", [int, float, str, bool])
def test_parse_multiple_without_required_container_arguments(container_type: Type, item_type: Type):
    @dataclass
    class SomeClass(TestSetup):
        a: container_type[item_type]  # type: ignore
        """some docstring for attribute 'a'"""
    with raises():
        _ = SomeClass.setup_multiple(3, "")


@parametrize("container_type", [List, Tuple])
@parametrize("item_type", [int, float, str, bool])
def test_parse_multiple_with_arg_name_without_arg_value(container_type: Type, item_type: Type):
    @dataclass
    class SomeClass(TestSetup):
        a: container_type[item_type]  # type: ignore
        """some docstring for attribute 'a'"""

    with raises():
        _ = SomeClass.setup_multiple(3, "--a")

@xfail(reason="BUG: When # of instances to parse is equal to item count in default value.")
@parametrize("num_instances", [1, 2, 3, 5])
@parametrize("container_type, default_value", [
    (List[str], ["1", "2", "3"]),
    (List[str], ["1", "2"]),
    (Tuple[str, int], ["1", 2]),
    (List[Union[str, bool]], ["1", False]),
])
def test_parse_multiple_containers_default_value(
        num_instances: int,
        container_type: Type[Container],
        default_value: Container
):
    @dataclass
    class SomeClass(TestSetup):
        a: container_type = field(default_factory=lambda: default_value.copy())  # type: ignore
        """some docstring for attribute 'a'"""

    values = list(SomeClass.setup_multiple(num_instances))
    assert values == [SomeClass(default_value) for i in range(num_instances)]
