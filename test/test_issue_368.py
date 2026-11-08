"""Test for https://github.com/lebrice/SimpleParsing/issues/368."""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import simple_parsing


@dataclass
class Config:
    x: int = 1


def test_add_argument_group_does_not_warn():
    """Python 3.14 deprecates passing `prefix_chars` to `add_argument_group`."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        parser = simple_parsing.ArgumentParser()
        parser.add_arguments(Config, dest="config")
        args = parser.parse_args(["--x", "3"])
    assert args.config == Config(x=3)


def test_argument_group_inherits_parser_settings():
    parser = simple_parsing.ArgumentParser(
        prefix_chars="+", argument_default=123, conflict_handler="resolve"
    )
    group = parser.add_argument_group("group")
    assert group.prefix_chars == "+"
    assert group.argument_default == 123
    assert group.conflict_handler == "resolve"

    group.add_argument("+y", type=int)
    assert parser.parse_args(["+y", "4"]).y == 4
