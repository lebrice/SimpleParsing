"""Tests for the setdefaults method of the parser."""
import typing
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from simple_parsing.helpers.serialization.serializable import save, to_dict
from simple_parsing.parsing import ArgumentParser
from simple_parsing.wrappers.field_wrapper import NestedMode

if typing.TYPE_CHECKING:
    import yaml
else:
    yaml = pytest.importorskip("yaml")

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


def test_set_broken_defaults_from_file(tmp_path: Path):
    parser = ArgumentParser()
    parser.add_arguments(Foo, dest="foo")

    saved_config = Foo(a=456, b="HOLA")
    config_path = tmp_path / "broken_foo.yaml"
    broken_yaml = to_dict(saved_config)
    broken_yaml["i_do_not_exist"] = 3
    with open(config_path, "w") as f:
        yaml.dump({"foo": broken_yaml}, f)

    with pytest.raises(
        RuntimeError,
        match=(
            r"\['i_do_not_exist'\] are not fields of <class 'test.test_set_defaults.Foo'> at path 'foo'!"
        ),
    ):
        parser.set_defaults(config_path)


def test_set_defaults_from_file_without_root(tmp_path: Path):
    """Test that set_defaults accepts the fields of the dataclass directly, when the parser has
    nested_mode=NestedMode.WITHOUT_ROOT."""
    parser = ArgumentParser(nested_mode=NestedMode.WITHOUT_ROOT)
    parser.add_arguments(Foo, dest="foo")

    save_path = tmp_path / "temp.json"
    save(dict(a=456, b="BYE BYE"), path=save_path)

    parser.set_defaults(save_path)

    args = parser.parse_args("")
    assert args.foo == Foo(a=456, b="BYE BYE")

    args = parser.parse_args("--a 111".split())
    assert args.foo == Foo(a=111, b="BYE BYE")


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


@dataclass
class ConfigWithFoo(TestSetup):
    c: str = "bob"
    foo: Foo = field(default_factory=Foo)


@pytest.mark.parametrize("with_root", [True, False])
@pytest.mark.parametrize("add_arguments_before", [True, False])
def test_with_nested_field(tmp_path: Path, add_arguments_before: bool, with_root: bool):
    """Test that when we use set_defaults with a config that has a nested dataclass field, we can
    pass a path to a yaml file for one of the field, and it also works."""
    parser = ArgumentParser(
        nested_mode=NestedMode.WITHOUT_ROOT if not with_root else NestedMode.DEFAULT
    )
    if add_arguments_before:
        parser.add_arguments(ConfigWithFoo, dest="config")

    save_path = tmp_path / "temp.json"
    from simple_parsing.helpers.serialization import encode

    saved_config = ConfigWithFoo(foo=Foo(a=456, b="BYE BYE"))

    if with_root:
        save(encode({"config": saved_config}), path=save_path)
    else:
        save(saved_config, path=save_path)
    parser.set_defaults(save_path)

    if not add_arguments_before:
        parser.add_arguments(ConfigWithFoo, dest="config")

    args = parser.parse_args("")
    assert args.config == saved_config

    args = parser.parse_args("--a 111".split())
    assert args.config == ConfigWithFoo(foo=Foo(a=111, b="BYE BYE"))
