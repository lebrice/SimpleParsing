""" Tests specific to the `parse` function.

NOTE: Currently, All the tests are ran using both the parse and ArgumentParser-style apis.
(for tests that don't use the TestSetup class, this doesn't change anything).
These
tests are
"""
from dataclasses import dataclass
from pathlib import Path

import pytest

from simple_parsing import Serializable, parse, subgroups
from simple_parsing.helpers.fields import field
from simple_parsing.helpers.serialization import save
from simple_parsing.parsing import ArgumentParser
from simple_parsing.wrappers.field_wrapper import NestedMode

from .testutils import TestSetup


@dataclass
class ModelConfig(TestSetup, Serializable):
    pass


@dataclass
class ModelAConfig(ModelConfig):
    lr: float = 3e-4
    num_blocks: int = 2


@dataclass
class ModelBConfig(ModelConfig):
    lr: float = 1e-3
    dropout: float = 0.1
    different_field: str = "bob"


@dataclass
class NestedConfig(TestSetup, Serializable):
    model: ModelAConfig = field(default_factory=ModelAConfig)


@dataclass
class ConfigWithSubgroups(TestSetup, Serializable):
    model: ModelConfig = subgroups(
        {"model_a": ModelAConfig, "model_b": ModelBConfig},
        default=ModelAConfig(),
    )


@pytest.mark.parametrize(
    "config",
    [
        ModelAConfig(),
        ModelAConfig(lr=1.23),
        NestedConfig(model=ModelAConfig(lr=1.23)),
        ConfigWithSubgroups(model=ModelAConfig(lr=4.56)),
    ],
)
@pytest.mark.parametrize("savefile_extension", ["yaml", "json", "pkl"])
def test_parse_uses_config_contents_as_defaults(
    tmp_path: Path,
    savefile_extension: str,
    config: TestSetup,
    parse_api: bool,
):
    savefile = tmp_path / f"config.{savefile_extension}"
    save(config, savefile)

    if parse_api:
        assert parse(type(config), args=[], config_path=savefile) == config

    else:
        # NOTE: Need to use `WITHOUT_ROOT` here so the command-line matches the file contents
        # (cli has 'config' as an implicit prefix)
        parser = ArgumentParser(config_path=savefile, nested_mode=NestedMode.WITHOUT_ROOT)
        parser.add_arguments(type(config), dest="config")
        args = parser.parse_args("")
        parsed_config = getattr(args, "config")
        assert parsed_config == config
