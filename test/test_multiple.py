import argparse
import dataclasses
import shlex
from dataclasses import dataclass, field
from typing import *

import pytest

from simple_parsing import (Formatter, InconsistentArgumentError,
                            ParseableFromCommandLine)

from .testutils import TestSetup

@pytest.mark.parametrize(
    "num_instances", [
        pytest.mark.xfail(
            (1,), reason="I don't know if this should handle a single instance to parse.."),
        2,
        5,
        50]
)
@pytest.mark.parametrize(
    "some_type, default_value",
    [
        (int,   123524),
        (float, 123.456),
        (str,   "bob"),
        (bool,  True),
    ]
)
def test_parse_multiple_with_no_arguments_sets_default_value(num_instances: int, some_type: Type, default_value: Any):
    @dataclass()
    class SomeClass(ParseableFromCommandLine, TestSetup):
        a: some_type = default_value  # type: ignore
        """some docstring for attribute 'a'"""

    args = SomeClass.setup("", multiple=True)
    classes = SomeClass.from_args_multiple(args, num_instances)

    assert len(classes) == num_instances
    for i in range(num_instances):
        c_i = classes[i]
        assert c_i.a == default_value
        assert isinstance(c_i.a, some_type)


@pytest.mark.parametrize(
    "num_instances", [
        pytest.mark.xfail((1,), reason="I don't know if this should be handled."),
        2,
        5,
        50]
)
@pytest.mark.parametrize(
    "some_type, default_value,  passed_value",
    [
        (int,   123524,     12),
        (float, 123.456,    -12.3),
        (str,   "bob",      "random"),
        (bool,  True,       False),
    ]
)
def test_parse_multiple_with_single_arg_value_sets_that_value_for_all_instances(
        num_instances: int,
        some_type: Type,
        default_value: Any,
        passed_value: Any
    ):

    @dataclass()
    class SomeClass(ParseableFromCommandLine, TestSetup):
        a: some_type = default_value  # type: ignore
        """some docstring for attribute 'a'"""

    args = SomeClass.setup(f"--a {passed_value}", multiple=True)
    classes = SomeClass.from_args_multiple(args, num_instances)

    assert len(classes) == num_instances
    for i in range(num_instances):
        c_i = classes[i]
        assert c_i.a == passed_value
        assert isinstance(c_i.a, some_type)


@pytest.mark.parametrize(
    "some_type, default_value,  passed_values",
    [
        (int,   123524,     [1, 2, 3]),
        (float, 123.456,    [4.5, -12.3, 9]),
        (str,   "bob",      ["random", "triceratops", "cocobongo"]),
        (bool,  True,       [False, True, False]),
    ]
)
def test_parse_multiple_with_provided_value_for_each_instance(
        some_type: Type,
        default_value: Any,
        passed_values: List[Any]
    ):

    @dataclass()
    class SomeClass(ParseableFromCommandLine, TestSetup):
        a: some_type = default_value  # type: ignore
        """some docstring for attribute 'a'"""

    args = SomeClass.setup(f"--a {' '.join(str(p) for p in passed_values)}", multiple=True)
    classes = SomeClass.from_args_multiple(args, 3)

    assert len(classes) == 3
    for i in range(3):
        c_i = classes[i]
        assert c_i.a == passed_values[i]
        assert isinstance(c_i.a, some_type)
