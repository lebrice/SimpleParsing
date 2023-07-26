from pathlib import Path
import shlex
import pytest
import yaml
from dataclasses import dataclass
from simple_parsing import subgroups, ArgumentParser
from simple_parsing.wrappers.field_wrapper import (
    ArgumentGenerationMode,
    DashVariant,
    NestedMode,
)

from simple_parsing.helpers.serialization.serializable import to_dict


@dataclass
class A:
    a: int = 0


@dataclass
class B1(A):
    b: float = 1


@dataclass
class B2(A):
    b: float = 2


@dataclass
class C:
    c: A = subgroups(
        {
            "b1": B1,
            "b2": B2,
        },
        default="b1",
    )


@pytest.mark.parametrize(
    ("argv", "expected", "save_dc_types_in_config"),
    [
        pytest.param(
            "",
            C(c=B2(a=0, b=1)),
            True,
            # marks=pytest.mark.xfail(strict=True, raises=AssertionError),
        ),
        pytest.param(
            "--c.a=1",
            C(c=B2(a=1, b=1)),
            True,
            marks=pytest.mark.xfail(strict=True, raises=AssertionError),
        ),
        pytest.param(
            "--c=b1",
            C(c=B1(a=0, b=1)),
            True,
            marks=pytest.mark.xfail(strict=True, raises=RuntimeError),
        ),
    ],
)
def test_reproduce_issue(tmp_path: Path, argv: str, expected: C, save_dc_types_in_config: bool):
    """Test for https://github.com/lebrice/SimpleParsing/issues/276."""
    config_path = tmp_path / "config.yaml"
    config_contents = to_dict(C(c=B2(a=0, b=1)), save_dc_types=save_dc_types_in_config)
    with open(config_path, "w") as f:
        yaml.dump(config_contents, f, indent=4)

    parser = ArgumentParser(
        argument_generation_mode=ArgumentGenerationMode.NESTED,
        nested_mode=NestedMode.WITHOUT_ROOT,
        add_option_string_dash_variants=DashVariant.UNDERSCORE_AND_DASH,
        config_path=config_path,
    )
    parser.add_arguments(C, dest="config")
    args = parser.parse_args(shlex.split(argv))
    config: C = args.config
    assert config == expected
