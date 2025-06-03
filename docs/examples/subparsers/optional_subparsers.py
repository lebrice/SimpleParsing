from dataclasses import dataclass
from typing import Union

from simple_parsing import ArgumentParser
from simple_parsing.helpers.fields import subparsers


@dataclass
class AConfig:
    foo: int = 123


@dataclass
class BConfig:
    bar: float = 4.56


@dataclass
class Options:
    config: Union[AConfig, BConfig] = subparsers(
        {"a": AConfig, "b": BConfig}, default_factory=AConfig
    )


def main():
    parser = ArgumentParser()

    parser.add_arguments(Options, dest="options")

    # Equivalent to:
    # subparsers = parser.add_subparsers(title="config", required=False)
    # parser.set_defaults(config=AConfig())
    # a_parser = subparsers.add_parser("a", help="A help.")
    # a_parser.add_arguments(AConfig, dest="config")
    # b_parser = subparsers.add_parser("b", help="B help.")
    # b_parser.add_arguments(BConfig, dest="config")

    args = parser.parse_args()

    print(args)
    options: Options = args.options
    print(options)


main()
expected = """
Namespace(options=Options(config=AConfig(foo=123)))
Options(config=AConfig(foo=123))
"""
