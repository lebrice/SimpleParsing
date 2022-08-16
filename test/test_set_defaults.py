""" Tests for the setdefaults method of the parser. """
from dataclasses import dataclass
from pathlib import Path

import yaml

from simple_parsing.helpers.serialization.serializable import to_dict
from simple_parsing.parsing import ArgumentParser

from .testutils import TestSetup


@dataclass
class Foo(TestSetup):
    a: int = 123
    b: str = "hello"


def test_set_defaults():
    parser = ArgumentParser()
    parser.add_arguments(Foo, dest="foo")
    parser.set_defaults(foo=Foo(b="HOLA"))
    args = parser.parse_args("")
    assert args.foo == Foo(b="HOLA")


def test_set_defaults_from_file(tmp_path: Path):
    parser = ArgumentParser()
    parser.add_arguments(Foo, dest="foo")

    saved_config = Foo(a=456, b="HOLA")
    config_path = tmp_path / "foo.yaml"
    with open(config_path, "w") as f:
        yaml.dump({"foo": to_dict(saved_config)}, f)

    parser.set_defaults(config_path)
    args = parser.parse_args("")
    assert args.foo == saved_config


def test_set_defaults_from_file_before_adding_args(tmp_path: Path):
    parser = ArgumentParser()

    saved_config = Foo(a=456, b="HOLA")
    config_path = tmp_path / "foo.yaml"
    with open(config_path, "w") as f:
        yaml.dump({"foo": to_dict(saved_config)}, f)
    parser.set_defaults(config_path)

    parser.add_arguments(Foo, dest="foo")
    args = parser.parse_args("")
    assert args.foo == saved_config
