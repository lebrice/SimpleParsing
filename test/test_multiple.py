import argparse
import dataclasses
import shlex
from dataclasses import dataclass, field
from typing import *

import pytest

from simple_parsing import (Formatter, InconsistentArgumentError,
                            ParseableFromCommandLine)

from .testutils import TestSetup

@pytest.mark.parametrize("num_instances", [1, 2, 5, 50])
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


@pytest.mark.parametrize("num_instances", [2, 5, 50])
@pytest.mark.parametrize(
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
    ])
def test_parse_multiple_with_provided_value_for_each_instance(
        some_type: Type,
        default_value: Any,
        passed_values: List[Any]
    ):

    @dataclass()
    class SomeClass(ParseableFromCommandLine, TestSetup):
        a: some_type = default_value  # type: ignore
        """some docstring for attribute 'a'"""
    # TODO: maybe test out other syntaxes for passing in multiple argument values? (This looks a lot like passing in a list of values..)
    arguments = f"--a {' '.join(str(p) for p in passed_values)}"
    args = SomeClass.setup(arguments, multiple=True)
    classes = SomeClass.from_args_multiple(args, 3)

    assert len(classes) == 3
    for i in range(3):
        c_i = classes[i]
        assert c_i.a == passed_values[i]
        assert isinstance(c_i.a, some_type)


@pytest.mark.parametrize("some_type", [int, float, str, bool])        
def test_parse_multiple_without_required_arguments(some_type: Type):
    @dataclass()
    class SomeClass(ParseableFromCommandLine, TestSetup):
        a: some_type # type: ignore
        """some docstring for attribute 'a'"""

    with pytest.raises(SystemExit):
        args = SomeClass.setup("", multiple=True)

@pytest.mark.parametrize("container_type, concrete_type", [(List, list), (Tuple, tuple)])
@pytest.mark.parametrize("item_type", [int, float, str, bool])
def test_parse_multiple_without_required_container_arguments(container_type: Type, concrete_type: Type, item_type: Type):
    @dataclass()
    class SomeClass(ParseableFromCommandLine, TestSetup):
        a: container_type[item_type] # type: ignore
        """some docstring for attribute 'a'"""

    with pytest.raises(SystemExit):
        args = SomeClass.setup("", multiple=True)


@pytest.mark.parametrize("some_type", [int, float, str])
def test_parse_multiple_with_argument_name_but_without_value(some_type: Type):
    @dataclass()
    class SomeClass(ParseableFromCommandLine, TestSetup):
        a: some_type # type: ignore
        """some docstring for attribute 'a'"""

    with pytest.raises(SystemExit):
        args = SomeClass.setup("--a", multiple=True)


def format_using_brackets(list_of_lists: List[List[Any]])-> str:
    return " ".join(
        f"[{','.join(str(p) for p in value_list)}]"
        for value_list in list_of_lists
    )


def format_using_single_quotes(list_of_lists: List[List[Any]])-> str:
    return " ".join(
        f"'{' '.join(str(p) for p in value_list)}'"
        for value_list in list_of_lists
    )


def format_using_double_quotes(list_of_lists: List[List[Any]])-> str:
    return " ".join(
        f'"{" ".join(str(p) for p in value_list)}"'
        for value_list in list_of_lists
    )

ListFormattingFunction = Callable[[List[List[Any]]], str]

@pytest.mark.parametrize(
    "list_formatting_function",
    [
        format_using_brackets,
        format_using_single_quotes,
        format_using_double_quotes,
    ])
@pytest.mark.parametrize(
    "item_type, passed_values",
    [
        (int,   [[1, 2], [4, 5], [7, 8]]),
        (float, [[1.1, 2.1], [4.2, 5.2], [7.2, 8.2]]),
        (str,   [["a", "b"], ["c", "d"], ["e", "f"]]),
        # (bool,  [[True, True], [True, False], [False, True]]),
    ]
)
def test_parse_multiple_with_list_attributes(
        list_formatting_function: ListFormattingFunction,
        item_type: Type,
        passed_values: List[List[Any]],
    ):
    @dataclass()
    class SomeClass(ParseableFromCommandLine, TestSetup):
        a: List[item_type] = field(default_factory=list)  # type: ignore
        """some docstring for attribute 'a'"""

    arguments = "--a " + list_formatting_function(passed_values)
    print(arguments)

    args = SomeClass.setup(arguments, multiple=True)
    classes = SomeClass.from_args_multiple(args, 3)

    assert len(classes) == 3
    for i, c_i in enumerate(classes):
        assert c_i.a == passed_values[i]
        assert len(c_i.a) == 2
        assert all(
            isinstance(v, item_type) for v in c_i.a
        )
