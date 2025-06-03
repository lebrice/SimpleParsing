from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from simple_parsing import ArgumentParser, subgroups
from simple_parsing.wrappers.field_wrapper import ArgumentGenerationMode, NestedMode


@dataclass
class ModelConfig:
    ...


@dataclass
class DatasetConfig:
    ...


@dataclass
class ModelAConfig(ModelConfig):
    lr: float = 3e-4
    optimizer: str = "Adam"
    betas: tuple[float, float] = (0.9, 0.999)


@dataclass
class ModelBConfig(ModelConfig):
    lr: float = 1e-3
    optimizer: str = "SGD"
    momentum: float = 1.234


@dataclass
class Dataset1Config(DatasetConfig):
    data_dir: str | Path = "data/foo"
    foo: bool = False


@dataclass
class Dataset2Config(DatasetConfig):
    data_dir: str | Path = "data/bar"
    bar: float = 1.2


@dataclass
class Config:
    # Which model to use
    model: ModelConfig = subgroups(
        {"model_a": ModelAConfig, "model_b": ModelBConfig},
        default_factory=ModelAConfig,
    )

    # Which dataset to use
    dataset: DatasetConfig = subgroups(
        {"dataset_1": Dataset1Config, "dataset_2": Dataset2Config},
        default_factory=Dataset2Config,
    )


parser = ArgumentParser(
    argument_generation_mode=ArgumentGenerationMode.NESTED, nested_mode=NestedMode.WITHOUT_ROOT
)
parser.add_arguments(Config, dest="config")
args = parser.parse_args()

config: Config = args.config

print(config)
expected = """
Config(model=ModelAConfig(lr=0.0003, optimizer='Adam', betas=(0.9, 0.999)), dataset=Dataset2Config(data_dir='data/bar', bar=1.2))
"""

parser.print_help()
expected += """
usage: subgroups_example.py [-h] [--model {model_a,model_b}] [--dataset {dataset_1,dataset_2}] [--model.lr float] [--model.optimizer str] [--model.betas float float]
                            [--dataset.data_dir str|Path] [--dataset.bar float]

options:
  -h, --help            show this help message and exit

Config ['config']:
  Config(model: 'ModelConfig' = ModelAConfig(lr=0.0003, optimizer='Adam', betas=(0.9, 0.999)), dataset: 'DatasetConfig' = Dataset2Config(data_dir='data/bar', bar=1.2))

  --model {model_a,model_b}
                        Which model to use (default: ModelAConfig(lr=0.0003, optimizer='Adam', betas=(0.9, 0.999)))
  --dataset {dataset_1,dataset_2}
                        Which dataset to use (default: Dataset2Config(data_dir='data/bar', bar=1.2))

ModelAConfig ['config.model']:
  ModelAConfig(lr: 'float' = 0.0003, optimizer: 'str' = 'Adam', betas: 'tuple[float, float]' = (0.9, 0.999))

  --model.lr float      (default: 0.0003)
  --model.optimizer str
                        (default: Adam)
  --model.betas float float
                        (default: (0.9, 0.999))

Dataset2Config ['config.dataset']:
  Dataset2Config(data_dir: 'str | Path' = 'data/bar', bar: 'float' = 1.2)

  --dataset.data_dir str|Path
                        (default: data/bar)
  --dataset.bar float   (default: 1.2)
"""
