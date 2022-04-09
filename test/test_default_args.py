import argparse
from dataclasses import dataclass

from simple_parsing import ArgumentParser
from simple_parsing.utils import str2bool
from .testutils import raises_missing_required_arg, shlex


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
    parser.add_arguments(SomeClass, dest="some_class", default=SomeClass(a=expected_value))

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


def test_suppress_default(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type
        b: int = 5

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest='some_class', default=argparse.SUPPRESS)

    parsed_args, unparsed_args = parser.parse_known_args(shlex.split(f'--a {passed_value} --b 0'))
    assert parsed_args == argparse.Namespace(some_class={'a': expected_value, 'b': 0})
    assert unparsed_args == []

    parsed_args, unparsed_args = parser.parse_known_args(shlex.split(f'--a {passed_value}'))
    assert parsed_args == argparse.Namespace(some_class={'a': expected_value})
    assert unparsed_args == []

    assert parser.parse_args('') == argparse.Namespace()
    assert parser.parse_args(shlex.split('--b 0')) == argparse.Namespace(some_class={'b': 0})


def test_suppress_with_regular_suppressed_args(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type
        b: int = 5

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest='some_class', default=argparse.SUPPRESS)
    if some_type == bool:
        parser.add_argument('--c', type=str2bool, default=argparse.SUPPRESS)
    else:
        parser.add_argument('--c', type=some_type, default=argparse.SUPPRESS)

    parsed_args, unparsed_args = parser.parse_known_args(
        shlex.split(f'--a {passed_value} --b 0 --c {passed_value}')
    )
    assert parsed_args == argparse.Namespace(some_class={'a': expected_value, 'b': 0}, c=expected_value)
    assert unparsed_args == []

    parsed_args, unparsed_args = parser.parse_known_args(shlex.split(f'--a {passed_value}'))
    assert parsed_args == argparse.Namespace(some_class={'a': expected_value})
    assert unparsed_args == []

    parsed_args, unparsed_args = parser.parse_known_args(
        shlex.split(f'--a {passed_value} --c {passed_value}')
    )
    assert parsed_args == argparse.Namespace(some_class={'a': expected_value}, c=expected_value)
    assert unparsed_args == []

    assert parser.parse_args('') == argparse.Namespace()
    assert parser.parse_args(shlex.split('--b 0')) == argparse.Namespace(some_class={'b': 0})


def test_suppress_with_regular_unsuppressed_args(simple_attribute, silent):
    some_type, passed_value, expected_value = simple_attribute

    @dataclass
    class SomeClass:
        a: some_type
        b: int = 5

    parser = ArgumentParser()
    parser.add_arguments(SomeClass, dest='some_class', default=argparse.SUPPRESS)
    if some_type == bool:
        parser.add_argument('--c', type=str2bool)
    else:
        parser.add_argument('--c', type=some_type)

    parsed_args, unparsed_args = parser.parse_known_args(
        shlex.split(f'--a {passed_value} --b 0 --c {passed_value}')
    )
    assert parsed_args == argparse.Namespace(some_class={'a': expected_value, 'b': 0}, c=expected_value)
    assert unparsed_args == []

    parsed_args, unparsed_args = parser.parse_known_args(shlex.split(f'--a {passed_value}'))
    assert parsed_args == argparse.Namespace(some_class={'a': expected_value}, c=None)
    assert unparsed_args == []

    parsed_args, unparsed_args = parser.parse_known_args(
        shlex.split(f'--a {passed_value} --c {passed_value}')
    )
    assert parsed_args == argparse.Namespace(some_class={'a': expected_value}, c=expected_value)
    assert unparsed_args == []

    assert parser.parse_args('') == argparse.Namespace(c=None)
    assert parser.parse_args(shlex.split('--b 0')) == argparse.Namespace(some_class={'b': 0}, c=None)


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
    parser.add_arguments(SomeClass, dest='some_class', default=argparse.SUPPRESS)

    parsed_args, unparsed_args = parser.parse_known_args(shlex.split(f'--c {passed_value} --b 0'))
    assert parsed_args == argparse.Namespace(some_class={'a': {'c': expected_value}, 'b': 0})
    assert unparsed_args == []

    parsed_args, unparsed_args = parser.parse_known_args(shlex.split(f'--c {passed_value} --b 0'))
    assert parsed_args == argparse.Namespace(some_class={'a': {'c': expected_value}, 'b': 0})
    assert unparsed_args == []

    parsed_args, unparsed_args = parser.parse_known_args(shlex.split(f'--c {passed_value}'))
    assert parsed_args == argparse.Namespace(some_class={'a': {'c': expected_value}})
    assert unparsed_args == []

    assert parser.parse_args('') == argparse.Namespace()
    assert parser.parse_args(shlex.split('--b 0')) == argparse.Namespace(some_class={'b': 0})

    parsed_args = parser.parse_args(shlex.split(f'--c {passed_value}'))
    assert parsed_args == argparse.Namespace(some_class={'a': {'c': expected_value}})
