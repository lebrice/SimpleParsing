"""Tests for serialization to/from yaml files."""
import textwrap
from dataclasses import dataclass

import pytest

from simple_parsing import list_field

yaml = pytest.importorskip("yaml")

from simple_parsing.helpers.serialization.yaml_serialization import YamlSerializable  # noqa: E402


@dataclass
class Point(YamlSerializable):
    x: int = 0
    y: int = 0


@dataclass
class Config(YamlSerializable):
    name: str = "train"
    bob: int = 123
    some_float: float = 1.23

    points: list[Point] = list_field()


def test_dumps():
    p1 = Point(x=1, y=6)
    p2 = Point(x=3, y=1)
    config = Config(name="heyo", points=[p1, p2])
    assert config.dumps() == textwrap.dedent(
        """\
        bob: 123
        name: heyo
        points:
        - x: 1
          y: 6
        - x: 3
          y: 1
        some_float: 1.23
        """
    )


def test_dumps_loads():
    p1 = Point(x=1, y=6)
    p2 = Point(x=3, y=1)
    config = Config(name="heyo", points=[p1, p2])
    assert Config.loads(config.dumps()) == config

    assert config == Config.loads(
        textwrap.dedent(
            """\
        bob: 123
        name: heyo
        points:
        - x: 1
          y: 6
        - x: 3
          y: 1
        some_float: 1.23
        """
        )
    )


# def test_save_yml(HyperParameters, tmpdir: Path):
#     hparams = HyperParameters.setup("")
#     tmp_path = Path(tmpdir / "temp.pth")
#     hparams.save(tmp_path)

#     _hparams = HyperParameters.load(tmp_path)
#     assert hparams == _hparams
