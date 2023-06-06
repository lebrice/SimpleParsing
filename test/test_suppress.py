import argparse
import shlex
from dataclasses import dataclass
from test.testutils import raises_missing_required_arg

from simple_parsing import ArgumentParser
from simple_parsing.utils import str2bool


def test_suppress_default(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type
        b: int = 5

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest="some_class", default=argparse.SUPPRESS)

    parsed_args, unparsed_args = parser.parse_known_args(shlex.split(f"--a {passed_value} --b 0"))
    assert parsed_args == argparse.Namespace(some_class={"a": expected_value, "b": 0})
    assert unparsed_args == []

    parsed_args, unparsed_args = parser.parse_known_args(shlex.split(f"--a {passed_value}"))
    assert parsed_args == argparse.Namespace(some_class={"a": expected_value})
    assert unparsed_args == []

    assert parser.parse_args("") == argparse.Namespace()
    assert parser.parse_args(shlex.split("--b 0")) == argparse.Namespace(some_class={"b": 0})


def test_with_unsuppressed_dataclass(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass1:
        a: some_type
        b: int = 5

    @dataclass
    class SomeClass2:
        c: some_type
        d: int = 5

    parser = ArgumentParser()
    parser.add_arguments(SomeClass1, dest="some_class1", default=argparse.SUPPRESS)
    parser.add_arguments(SomeClass2, dest="some_class2")

    parsed_args = parser.parse_args(shlex.split(f"--a {passed_value} --b 0 --c {passed_value}"))
    assert parsed_args == argparse.Namespace(
        some_class1={"a": expected_value, "b": 0},
        some_class2=SomeClass2(c=expected_value),
    )

    parsed_args = parser.parse_args(shlex.split(f"--a {passed_value} --c {passed_value}"))
    assert parsed_args == argparse.Namespace(
        some_class1={"a": expected_value},
        some_class2=SomeClass2(c=expected_value),
    )

    with raises_missing_required_arg("-c/--c"):
        parser.parse_args(shlex.split(f"--a {passed_value}"))

    with raises_missing_required_arg("-c/--c"):
        parser.parse_args("")

    assert parser.parse_args(shlex.split(f"--c {passed_value}")) == argparse.Namespace(
        some_class2=SomeClass2(expected_value)
    )


def test_conflict_with_unsuppressed_dataclass(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type
        b: int = 5

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest="some_class1", default=argparse.SUPPRESS)
    parser.add_arguments(SomeClass, dest="some_class2")

    parsed_args = parser.parse_args(
        shlex.split(
            f"--some_class1.a {passed_value} --some_class1.b 0 --some_class2.a {passed_value}"
        )
    )
    assert parsed_args == argparse.Namespace(
        some_class1={"a": expected_value, "b": 0},
        some_class2=SomeClass(expected_value),
    )

    parsed_args, unparsed_args = parser.parse_known_args(
        shlex.split(f"--a {passed_value} --some_class2.a {passed_value}")
    )
    assert parsed_args == argparse.Namespace(some_class2=SomeClass(expected_value))
    assert unparsed_args == shlex.split(f"--a {passed_value}")

    with raises_missing_required_arg("-some_class2.a/--some_class2.a"):
        parser.parse_known_args(shlex.split(f"--a {passed_value}"))

    with raises_missing_required_arg("-some_class2.a/--some_class2.a"):
        parser.parse_args("")

    assert parser.parse_args(shlex.split(f"--some_class2.a {passed_value}")) == argparse.Namespace(
        some_class2=SomeClass(expected_value)
    )


def test_with_regular_suppressed_args(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type
        b: int = 5

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest="some_class", default=argparse.SUPPRESS)
    if some_type == bool:
        parser.add_argument("--c", type=str2bool, default=argparse.SUPPRESS)
    else:
        parser.add_argument("--c", type=some_type, default=argparse.SUPPRESS)

    parsed_args = parser.parse_args(shlex.split(f"--a {passed_value} --b 0 --c {passed_value}"))
    assert parsed_args == argparse.Namespace(
        some_class={"a": expected_value, "b": 0}, c=expected_value
    )

    parsed_args, unparsed_args = parser.parse_known_args(shlex.split(f"--a {passed_value}"))
    assert parsed_args == argparse.Namespace(some_class={"a": expected_value})
    assert unparsed_args == []

    parsed_args = parser.parse_args(shlex.split(f"--a {passed_value} --c {passed_value}"))
    assert parsed_args == argparse.Namespace(some_class={"a": expected_value}, c=expected_value)

    assert parser.parse_args("") == argparse.Namespace()
    assert parser.parse_args(shlex.split("--b 0")) == argparse.Namespace(some_class={"b": 0})


def test_suppress_with_regular_unsuppressed_args(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type
        b: int = 5

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest="some_class", default=argparse.SUPPRESS)
    if some_type == bool:
        parser.add_argument("--c", type=str2bool)
    else:
        parser.add_argument("--c", type=some_type)

    parsed_args = parser.parse_args(shlex.split(f"--a {passed_value} --b 0 --c {passed_value}"))
    assert parsed_args == argparse.Namespace(
        some_class={"a": expected_value, "b": 0}, c=expected_value
    )

    parsed_args = parser.parse_args(shlex.split(f"--a {passed_value}"))
    assert parsed_args == argparse.Namespace(some_class={"a": expected_value}, c=None)

    parsed_args = parser.parse_args(shlex.split(f"--a {passed_value} --c {passed_value}"))
    assert parsed_args == argparse.Namespace(some_class={"a": expected_value}, c=expected_value)

    assert parser.parse_args("") == argparse.Namespace(c=None)
    assert parser.parse_args(shlex.split("--b 0")) == argparse.Namespace(
        some_class={"b": 0}, c=None
    )


def test_suppress_default_nested(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass()
    class SomeNestedClass:
        c: some_type

    @dataclass
    class SomeClass:
        a: SomeNestedClass
        b: int = 5

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest="some_class", default=argparse.SUPPRESS)

    parsed_args, unparsed_args = parser.parse_known_args(shlex.split(f"--c {passed_value} --b 0"))
    assert parsed_args == argparse.Namespace(some_class={"a": {"c": expected_value}, "b": 0})
    assert unparsed_args == []

    parsed_args, unparsed_args = parser.parse_known_args(shlex.split(f"--c {passed_value} --b 0"))
    assert parsed_args == argparse.Namespace(some_class={"a": {"c": expected_value}, "b": 0})
    assert unparsed_args == []

    parsed_args, unparsed_args = parser.parse_known_args(shlex.split(f"--c {passed_value}"))
    assert parsed_args == argparse.Namespace(some_class={"a": {"c": expected_value}})
    assert unparsed_args == []

    assert parser.parse_args("") == argparse.Namespace()
    assert parser.parse_args(shlex.split("--b 0")) == argparse.Namespace(some_class={"b": 0})

    parsed_args = parser.parse_args(shlex.split(f"--c {passed_value}"))
    assert parsed_args == argparse.Namespace(some_class={"a": {"c": expected_value}})
