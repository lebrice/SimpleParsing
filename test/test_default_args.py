from dataclasses import dataclass

from .testutils import *


def test_no_default_argument(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest="some_class")

    args = parser.parse_args(shlex.split(f"--a {passed_value}"))
    assert args == argparse.Namespace(some_class=SomeClass(a=expected_value))

    with raises_missing_required_arg():
        parser.parse_args("")


def test_default_dataclass_argument(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type

    parser = ArgumentParser()
    parser.add_arguments(
        SomeClass, dest="some_class", default=SomeClass(a=expected_value)
    )

    args = parser.parse_args("")
    assert args == argparse.Namespace(some_class=SomeClass(a=expected_value))


def test_default_dict_argument(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest="some_class", default={"a": expected_value})

    args = parser.parse_args("")
    assert args == argparse.Namespace(some_class=SomeClass(a=expected_value))


def test_default_dict_argument_override_cmdline(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest="some_class", default={"a": 0})

    args = parser.parse_args(shlex.split(f"--a {passed_value}"))
    assert args == argparse.Namespace(some_class=SomeClass(a=expected_value))


def test_partial_default_dict_argument(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type
        b: int

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest="some_class", default={"a": expected_value})

    args = parser.parse_args(shlex.split("--b 0"))
    assert args == argparse.Namespace(some_class=SomeClass(a=expected_value, b=0))
    with raises_missing_required_arg():
        parser.parse_args(shlex.split(f"--a {passed_value}"))
    with raises_missing_required_arg():
        parser.parse_args("")
