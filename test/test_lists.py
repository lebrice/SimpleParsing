from contextlib import suppress
from argparse import ArgumentError
from dataclasses import dataclass, field
from typing import *

import pytest

import simple_parsing
from simple_parsing import ArgumentParser, InconsistentArgumentError
from simple_parsing.helpers import list_field
from .testutils import *


def test_list_one_element(simple_attribute):
    some_type, passed_value, expected_value = simple_attribute
    
    @dataclass
    class Container(TestSetup):
        a: List[some_type] = list_field()

    c = Container.setup("")
    assert c.a == []
    c = Container.setup(f"--a {passed_value}")
    assert c.a == [expected_value], Container.get_help_text()

@pytest.fixture
def ContainerClass():   
    @dataclass
    class ContainerClass(TestSetup):
        a: Tuple[int]
        b: List[int]
        c: Tuple[str] = tuple()
        d: List[int] = list_field()
    return ContainerClass

def test_single_element_list(ContainerClass):
    container = ContainerClass.setup("--a 1 --b 4 --c 7 --d 10")
    assert container.a == (1,)
    assert container.b == [4]
    assert container.c == ('7',)
    assert container.d == [10]


def test_required_attributes_works(ContainerClass):
    with raises_missing_required_arg():
        ContainerClass.setup("--b 4")

    with raises_missing_required_arg():
        ContainerClass.setup("--a 4")

    container = ContainerClass.setup("--a 4 --b 5")
    assert container == ContainerClass(a=(4,), b=[5])

def test_default_value(ContainerClass):
    container = ContainerClass.setup("--a 1 --b 4 5 6")
    assert container.a == (1,)
    assert container.b == [4, 5, 6]
    assert container.c == tuple()
    assert container.d == list()


@parametrize(
    "list_formatting_function",
    [
        format_list_using_spaces,
        # format_list_using_brackets,
        xfail_param(format_list_using_brackets,      reason="TODO: decide which syntax we want to allow for single lists."),
        xfail_param(format_list_using_double_quotes, reason="TODO: decide which syntax we want to allow for single lists."),
        xfail_param(format_list_using_single_quotes, reason="TODO: decide which syntax we want to allow for single lists."),
    ])
@parametrize(
    "item_type, passed_values",
    [
        (int,   [1, 2]),
        (float, [1.1, 2.1]),
        (str,   ["a", "b"]),
        (bool,  [True, True]),
    ])
def test_list_supported_formats(
        list_formatting_function: ListFormattingFunction,
        item_type: Type,
        passed_values: List[Any],
):

    @dataclass
    class SomeClass(TestSetup):
        a: List[item_type] = field(default_factory=list)  # type: ignore
        """some docstring for attribute 'a'"""

    arguments = "--a " + list_formatting_function(passed_values)
    print(arguments)

    some_class = SomeClass.setup(arguments)

    assert some_class.a == passed_values
    assert isinstance(some_class, SomeClass)
    assert len(some_class.a) == 2
    assert all(
        isinstance(v, item_type) for v in some_class.a
    )


@parametrize(
    "list_of_lists_formatting_function",
    [
        format_lists_using_brackets,
        format_lists_using_single_quotes,
        format_lists_using_double_quotes,
    ])
@parametrize(
    "item_type, passed_values",
    [
        (int,   [[1, 2], [4, 5], [7, 8]]),
        (float, [[1.1, 2.1], [4.2, 5.2], [7.2, 8.2]]),
        (str,   [["a", "b"], ["c", "d"], ["e", "f"]]),
        (bool,  [[True, True], [True, False], [False, True]]),
    ]
)
def test_parse_multiple_with_list_attributes(
        list_of_lists_formatting_function: ListOfListsFormattingFunction,
        item_type: Type,
        passed_values: List[List[Any]],
    ):

    @dataclass
    class SomeClass(TestSetup):
        a: List[item_type] = field(default_factory=list)  # type: ignore
        """some docstring for attribute 'a'"""

    arguments = "--a " + list_of_lists_formatting_function(passed_values)
    classes = list(SomeClass.setup_multiple(3, arguments))
    assert classes == [SomeClass(a=value) for value in passed_values]

