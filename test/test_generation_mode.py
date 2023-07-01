from dataclasses import dataclass

import pytest

from simple_parsing.wrappers.field_wrapper import ArgumentGenerationMode, NestedMode

from .testutils import TestSetup


@dataclass
class ModelOptions:
    path: str
    device: str


@dataclass
class ServerOptions(TestSetup):
    host: str
    port: int
    model: ModelOptions


expected = ServerOptions(host="myserver", port=80, model=ModelOptions(path="a_path", device="cpu"))


def test_flat():
    options = ServerOptions.setup(
        "--host myserver " "--port 80 " "--path a_path " "--device cpu",
    )
    assert options == expected

    with pytest.raises(SystemExit):
        ServerOptions.setup(
            "--opts.host myserver "
            "--opts.port 80 "
            "--opts.model.path a_path "
            "--opts.model.device cpu",
            dest="opts",
        )


@pytest.mark.parametrize("without_root", [True, False])
def test_both(without_root):
    options = ServerOptions.setup(
        "--host myserver " "--port 80 " "--path a_path " "--device cpu",
        dest="opts",
        argument_generation_mode=ArgumentGenerationMode.BOTH,
    )
    assert options == expected

    args = (
        "--opts.host myserver "
        "--opts.port 80 "
        "--opts.model.path a_path "
        "--opts.model.device cpu"
    )
    if without_root:
        args = args.replace("opts.", "")
    options = ServerOptions.setup(
        args,
        dest="opts",
        argument_generation_mode=ArgumentGenerationMode.BOTH,
        nested_mode=NestedMode.WITHOUT_ROOT if without_root else NestedMode.DEFAULT,
    )
    assert options == expected


@pytest.mark.parametrize("without_root", [True, False])
def test_nested(without_root):
    with pytest.raises(SystemExit):
        options = ServerOptions.setup(
            "--host myserver " "--port 80 " "--path a_path " "--device cpu",
            dest="opts",
            argument_generation_mode=ArgumentGenerationMode.NESTED,
        )

    args = (
        "--opts.host myserver "
        "--opts.port 80 "
        "--opts.model.path a_path "
        "--opts.model.device cpu"
    )
    if without_root:
        args = args.replace("opts.", "")
    options = ServerOptions.setup(
        args,
        dest="opts",
        argument_generation_mode=ArgumentGenerationMode.NESTED,
        nested_mode=NestedMode.WITHOUT_ROOT if without_root else NestedMode.DEFAULT,
    )
    assert options == expected
