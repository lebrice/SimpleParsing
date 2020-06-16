""" Tests for serialization to/from yaml files. """
from collections import OrderedDict
from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional, Tuple, Mapping, Type
from pathlib import Path
import pytest
import textwrap
from simple_parsing import mutable_field, list_field
from simple_parsing.helpers.serialization import YamlSerializable
from test.conftest import silent
import yaml

@dataclass
class Point(YamlSerializable):
    x: int = 0
    y: int = 0


@dataclass
class Config(YamlSerializable):
    name: str = "train"
    bob: int = 123
    some_float: float = 1.23

    points: List[Point] = list_field()


def test_dumps():
    p1 = Point(x=1, y=6)
    p2 = Point(x=3, y=1)
    config = Config(name="heyo", points=[p1, p2])
    assert config.dumps() == textwrap.dedent("""\
        bob: 123
        name: heyo
        points:
        - x: 1
          y: 6
        - x: 3
          y: 1
        some_float: 1.23
        """)


def test_dumps_loads():
    p1 = Point(x=1, y=6)
    p2 = Point(x=3, y=1)
    config = Config(name="heyo", points=[p1, p2])
    assert Config.loads(config.dumps()) == config
    
    assert config == Config.loads(textwrap.dedent("""\
        bob: 123
        name: heyo
        points:
        - x: 1
          y: 6
        - x: 3
          y: 1
        some_float: 1.23
        """))