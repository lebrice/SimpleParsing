"""Example where we compose different configurations!"""

import shlex
from dataclasses import dataclass

import simple_parsing


@dataclass
class Foo:
    a: str = "default value for `a` (from the dataclass definition of Foo)"


@dataclass
class Bar:
    b: str = "default value for `b` (from the dataclass definition of Bar)"


@dataclass
class Baz:
    c: str = "default value for `c` (from the dataclass definition of Baz)"


def main(args=None) -> None:
    """Example using composition of different configurations."""
    parser = simple_parsing.ArgumentParser(
        add_config_path_arg=True, config_path="composition_defaults.yaml"
    )

    parser.add_arguments(Foo, dest="foo")
    parser.add_arguments(Bar, dest="bar")
    parser.add_arguments(Baz, dest="baz")

    if isinstance(args, str):
        args = shlex.split(args)
    args = parser.parse_args(args)

    foo: Foo = args.foo
    bar: Bar = args.bar
    baz: Baz = args.baz
    print(f"foo: {foo}")
    print(f"bar: {bar}")
    print(f"baz: {baz}")


main()
expected = """
foo: Foo(a="default value for `a` from the Parser's `config_path` (composition_defaults.yaml)")
bar: Bar(b="default value for `b` from the Parser's `config_path` (composition_defaults.yaml)")
baz: Baz(c="default value for `c` from the Parser's `config_path` (composition_defaults.yaml)")
"""

main("--a 'Value passed from the command-line.' --config_path config_b.yaml")
expected += """\
foo: Foo(a='Value passed from the command-line.')
bar: Bar(b='default value for `b` from the config_b.yaml file')
baz: Baz(c="default value for `c` from the Parser's `config_path` (composition_defaults.yaml)")
"""

main("--a 'Value passed from the command-line.' --config_path config_a.yaml config_b.yaml")
expected += """\
foo: Foo(a='Value passed from the command-line.')
bar: Bar(b='default value for `b` from the config_b.yaml file')
baz: Baz(c="default value for `c` from the Parser's `config_path` (composition_defaults.yaml)")
"""
