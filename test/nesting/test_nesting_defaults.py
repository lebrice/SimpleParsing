import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from simple_parsing import ArgumentParser
from simple_parsing.helpers import field
from simple_parsing.helpers.serialization.serializable import Serializable

from ..testutils import needs_yaml


@dataclass
class AdvTraining(Serializable):
    epsilon: float
    iters: int


@dataclass
class DPTraining(Serializable):
    epsilon: float
    delta: float


@dataclass
class DatasetConfig(Serializable):
    name: str
    prop: str
    split: str = field(choices=["victim", "adv"])
    value: float
    drop_senstive_cols: Optional[bool] = False
    scale: Optional[float] = 1.0


@dataclass
class TrainConfig(Serializable):
    data_config: DatasetConfig
    epochs: int
    ...
    dp_config: Optional[DPTraining] = None
    adv_config: Optional[AdvTraining] = None
    ...
    cpu: bool = False


@needs_yaml
def test_comment_pull115(tmp_path):
    config_in_file = TrainConfig(
        data_config=DatasetConfig(name="bob", split="victim", prop="123", value=1.23),
        epochs=1,
    )
    config_in_file.save(tmp_path / "config.yaml")

    parser = ArgumentParser(add_help=False)
    parser.add_argument("--config_file", help="Specify config file", type=Path)
    args, remaining_argv = parser.parse_known_args(
        shlex.split(
            f"--config_file {tmp_path / 'config.yaml'} --cpu --epochs 2 --name bob "
            f"--prop 123 --value 1.23 --split victim "
            f"--drop_senstive_cols True --scale 1.0 --epochs 2 "
            f"--dp_config.epsilon 0.1 --delta 0.2 --adv_config.epsilon 0.1 "
            f"--iters 10"
        )
    )

    # Attempt to extract as much information from config file as you can
    config = TrainConfig.load(args.config_file, drop_extra_fields=False)
    # Also give user the option to provide config values over CLI
    parser = ArgumentParser(parents=[parser])
    parser.add_arguments(TrainConfig, dest="train_config", default=config)
    args = parser.parse_args(remaining_argv)

    config_in_args = TrainConfig(
        data_config=DatasetConfig(
            name="bob",
            split="victim",
            prop="123",
            value=1.23,
            drop_senstive_cols=True,
            scale=1.0,
        ),
        epochs=2,
        cpu=True,
        adv_config=AdvTraining(epsilon=0.1, iters=10),
        dp_config=DPTraining(epsilon=0.1, delta=0.2),
    )

    expected_dict = config_in_file.to_dict()
    expected_dict.update(config_in_args.to_dict())

    assert args.train_config.to_dict() == expected_dict
    assert args.train_config == TrainConfig.from_dict(expected_dict)
