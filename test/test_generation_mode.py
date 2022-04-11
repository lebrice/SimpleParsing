from dataclasses import dataclass
from pathlib import Path

import pytest

from simple_parsing.wrappers.field_wrapper import ArgumentGenerationMode, NestedMode
from . import TestSetup


@dataclass
class ModelOptions:
  path: str
  device: str


@dataclass
class ServerOptions(TestSetup):
  host: str
  port: int
  model: ModelOptions


def assert_as_expected(options: ServerOptions):
    assert isinstance(options, ServerOptions)
    assert options.host == "myserver"
    assert options.port == 80
    assert options.model.path == "a_path"
    assert options.model.device == "cpu"


def test_flat():
      options = ServerOptions.setup(
          "--host myserver " "--port 80 " "--path a_path " "--device cpu",
      )
      assert_as_expected(options)

      with pytest.raises(SystemExit):
          ServerOptions.setup(
              "--opts.host myserver " "--opts.port 80 " "--opts.model.path a_path " "--opts.model.device cpu",
              dest="opts"
          )


@pytest.mark.parametrize("without_root", [True, False])
def test_both(without_root):
    options = ServerOptions.setup(
        "--host myserver " "--port 80 " "--path a_path " "--device cpu",
        dest="opts",
        argument_generation_mode=ArgumentGenerationMode.BOTH
    )
    assert_as_expected(options)

    args = "--opts.host myserver " "--opts.port 80 " "--opts.model.path a_path " "--opts.model.device cpu"
    if without_root:
        args = args.replace("opts.", "")
    options = ServerOptions.setup(
        args,
        dest="opts",
        argument_generation_mode=ArgumentGenerationMode.BOTH,
        nested_mode=NestedMode.WITHOUT_ROOT if without_root else NestedMode.DEFAULT,
    )
    assert_as_expected(options)


@pytest.mark.parametrize("without_root", [True, False])
def test_nested(without_root):
    with pytest.raises(SystemExit):
        options = ServerOptions.setup(
            "--host myserver " "--port 80 " "--path a_path " "--device cpu",
            dest="opts",
            argument_generation_mode=ArgumentGenerationMode.NESTED
        )

    args = "--opts.host myserver " "--opts.port 80 " "--opts.model.path a_path " "--opts.model.device cpu"
    if without_root:
        args = args.replace("opts.", "")
    options = ServerOptions.setup(
        args,
        dest="opts",
        argument_generation_mode=ArgumentGenerationMode.NESTED,
        nested_mode=NestedMode.WITHOUT_ROOT if without_root else NestedMode.DEFAULT,
    )
    assert_as_expected(options)
