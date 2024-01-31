from dataclasses import dataclass
from pathlib import Path

import pytest

import simple_parsing

from .testutils import needs_yaml


@dataclass
class ConfigNested:
    a: str = "hello"


@dataclass
class Config:
    config_nested: ConfigNested


@needs_yaml
@pytest.mark.xfail(
    raises=RuntimeError,
    reason="This test raises a RuntimeError instead of the more expected TypeError",
)
def test_issue_295_unexpected_kwarg_should_raise_typeerror(tmp_path: Path):
    import yaml

    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"config_nested": {"a": "world", "b": 123}}))

    with pytest.raises(TypeError, match="got an unexpected keyword argument 'b'"):
        _ = simple_parsing.parse(Config, config_path=config_file)

    with pytest.raises(TypeError, match="got an unexpected keyword argument 'b'"):
        _ = simple_parsing.parse(
            Config, args=f"--config_path {config_file}", add_config_path_arg=True
        )


@needs_yaml
def test_issue_295_raises_runtime_error(tmp_path: Path):
    import yaml

    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"config_nested": {"a": "world", "b": 123}}))

    with pytest.raises(
        RuntimeError,
        match=rf"\['b'\] are not fields of {ConfigNested} at path 'config.config_nested'",
    ):
        _ = simple_parsing.parse(Config, config_path=config_file)

    with pytest.raises(
        RuntimeError,
        match=rf"\['b'\] are not fields of {ConfigNested} at path 'config.config_nested'",
    ):
        _ = simple_parsing.parse(
            Config, args=f"--config_path {config_file}", add_config_path_arg=True
        )
