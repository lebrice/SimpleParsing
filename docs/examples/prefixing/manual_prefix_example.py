from dataclasses import dataclass

from simple_parsing import ArgumentParser


@dataclass
class Config:
    """Simple example of a class that can be reused."""

    log_dir: str = "logs"


parser = ArgumentParser()
parser.add_arguments(Config, "train_config", prefix="train_")
parser.add_arguments(Config, "valid_config", prefix="valid_")
args = parser.parse_args()
print(vars(args))
