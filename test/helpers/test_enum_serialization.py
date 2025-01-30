import textwrap
import typing
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import pytest

from simple_parsing import Serializable
from simple_parsing.helpers.serialization.serializable import dumps_yaml, loads_yaml

if typing.TYPE_CHECKING:
    import yaml
else:
    yaml = pytest.importorskip("yaml")


class LoggingTypes(Enum):
    JSONL = "jsonl"
    PRINT = "print"


@dataclass
class Hparams:
    seed: int = 13
    xyz: list[LoggingTypes] = field(default_factory=list)


@dataclass
class Parameters(Serializable):
    hparams: Hparams = field(default_factory=Hparams)
    p: Optional[Path] = None


@pytest.mark.xfail(
    raises=KeyError, match="'jsonl'", strict=True, reason="Enums are saved by name, not by value."
)
def test_decode_enum_saved_by_value_doesnt_work(tmp_path: Path):
    """Test to reproduce
    https://github.com/lebrice/SimpleParsing/issues/219#issuecomment-1437817369."""
    with open(tmp_path / "conf.yaml", "w") as f:
        f.write(
            textwrap.dedent(
                """\
                p: /tmp
                hparams:
                    xyz:
                    - jsonl
                """
            )
        )

    file_config = Parameters.load_yaml(tmp_path / "conf.yaml")
    assert file_config == Parameters(hparams=Hparams(xyz=[LoggingTypes.JSONL]), p=Path("/tmp"))


def test_decode_enum_saved_by_name(tmp_path: Path):
    file = tmp_path / "conf.yaml"
    with open(file, "w") as f:
        f.write(
            textwrap.dedent(
                """\
                p: /tmp
                hparams:
                    xyz:
                    - JSONL
                """
            )
        )
    file_config = Parameters.load(file, load_fn=yaml.safe_load)
    assert file_config == Parameters(hparams=Hparams(xyz=[LoggingTypes.JSONL]), p=Path("/tmp"))


def test_round_trip():
    p = Parameters(hparams=Hparams(xyz=[LoggingTypes.JSONL]), p=Path("/tmp"))
    assert loads_yaml(Parameters, dumps_yaml(p)) == p
    assert dumps_yaml(loads_yaml(Parameters, dumps_yaml(p))) == dumps_yaml(p)


def test_decode_enum_saved_by_value_using_register(tmp_path: Path):
    from simple_parsing.helpers.serialization.decoding import register_decoding_fn
    from simple_parsing.helpers.serialization.encoding import encode

    register_decoding_fn(LoggingTypes, LoggingTypes)
    encode.register(LoggingTypes, lambda x: x.value)

    file = tmp_path / "conf.yaml"
    with open(file, "w") as f:
        f.write(
            textwrap.dedent(
                """\
                p: /tmp
                hparams:
                    xyz:
                    - jsonl
                """
            )
        )

    file_config = Parameters.load_yaml(file)
    assert file_config == Parameters(hparams=Hparams(xyz=[LoggingTypes.JSONL]), p=Path("/tmp"))


def test_decode_enum_saved_by_value_using_field(tmp_path: Path):
    from simple_parsing.helpers import field

    @dataclass
    class HparamsWithField:
        seed: int = 13
        xyz: list[LoggingTypes] = field(
            encoding_fn=lambda x: [e.value for e in x],
            decoding_fn=lambda str_list: [LoggingTypes(e) for e in str_list],
            default_factory=list,
        )

    @dataclass
    class ParametersWithField(Serializable):
        hparams: HparamsWithField = field(default_factory=HparamsWithField)
        p: Optional[Path] = None

    file = tmp_path / "conf.yaml"
    with open(file, "w") as f:
        f.write(
            textwrap.dedent(
                """\
                p: /tmp
                hparams:
                    xyz:
                    - jsonl
                """
            )
        )

    file_config = ParametersWithField.load_yaml(file)
    assert file_config == ParametersWithField(
        hparams=HparamsWithField(xyz=[LoggingTypes.JSONL]), p=Path("/tmp")
    )
