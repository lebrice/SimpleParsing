import argparse
import dataclasses
import shlex
from dataclasses import dataclass, field
from typing import *

import pytest

from simple_parsing import (InconsistentArgumentError,
                            ArgumentParser)

from .testutils import *

@parametrize("num_instances", [1, 2, 5])
@parametrize(
    "some_type, default_value",
    [
        (int,   123524),
        (float, 123.456),
        (str,   "bob"),
        (bool,  True),
    ]
)
def test_parse_multiple_with_no_arguments_sets_default_value(num_instances: int, some_type: Type, default_value: Any):
    @dataclass
    class SomeClass(TestSetup):
        a: some_type = default_value  # type: ignore
        """some docstring for attribute 'a'"""

    classes = SomeClass.setup_multiple(num_instances, "")
    assert len(classes) == num_instances
    for i in range(num_instances):
        c_i = classes[i]
        assert isinstance(c_i, SomeClass)
        assert c_i.a == default_value
        assert isinstance(c_i.a, some_type)


@parametrize("num_instances", [1, 2, 5])
@parametrize(
    "some_type, default_value,  passed_value",
    [
        (int,   123524,     12),
        (float, 123.456,    -12.3),
        (str,   "bob",      "random"),
        (bool,  True,       False),
    ])
def test_parse_multiple_with_single_arg_value_sets_that_value_for_all_instances(
        num_instances: int,
        some_type: Type,
        default_value: Any,
        passed_value: Any
    ):

    @dataclass
    class SomeClass(TestSetup):
        a: some_type = default_value  # type: ignore
        """some docstring for attribute 'a'"""
    classes = SomeClass.setup_multiple(num_instances, f"--a {passed_value}")

    assert len(classes) == num_instances
    for i in range(num_instances):
        c_i = classes[i]
        assert isinstance(c_i, SomeClass)
        assert c_i.a == passed_value
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
        passed_values: List[Any]
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
        a: some_type # type: ignore
        """some docstring for attribute 'a'"""

    with pytest.raises(SystemExit):
        some_class = SomeClass.setup_multiple(2, "")

@parametrize("container_type", [List, Tuple])
@parametrize("item_type", [int, float, str, bool])
def test_parse_multiple_without_required_container_arguments(container_type: Type, item_type: Type):
    @dataclass
    class SomeClass(TestSetup):
        a: container_type[item_type] # type: ignore
        """some docstring for attribute 'a'"""

    with pytest.raises(SystemExit):
        _ = SomeClass.setup_multiple(3, "")


@parametrize("container_type", [List, Tuple])
@parametrize("item_type", [int, float, str, bool])
def test_parse_multiple_with_arg_name_without_arg_value(container_type: Type, item_type: Type):
    @dataclass
    class SomeClass(TestSetup):
        a: container_type[item_type] # type: ignore
        """some docstring for attribute 'a'"""

    with pytest.raises(SystemExit):
        _ = SomeClass.setup_multiple(3, "--a")


