from dataclasses import dataclass

from simple_parsing import ArgumentParser
from simple_parsing.helpers import flag


def parse(cls, args: str = ""):
    """Removes some boilerplate code from the examples."""
    parser = ArgumentParser()  # Create an argument parser
    parser.add_arguments(cls, dest="hparams")  # add arguments for the dataclass
    ns = parser.parse_args(args.split())  # parse the given `args`
    return ns.hparams


@dataclass
class HParams:
    """Set of options for the training of a Model."""

    num_layers: int = 4
    num_units: int = 64
    optimizer: str = "ADAM"
    learning_rate: float = 0.001
    train: bool = flag(default=True, negative_prefix="--no-")


# Example 1 using default flag, i.e. train set to True
args = parse(HParams)

print(args)
expected = """
HParams(num_layers=4, num_units=64, optimizer='ADAM', learning_rate=0.001, train=True)
"""

# Example 2 using the flags negative prefix
assert parse(HParams, "--no-train") == HParams(train=False)


# showing what --help outputs
parser = ArgumentParser()  # Create an argument parser
parser.add_arguments(HParams, dest="hparams")  # add arguments for the dataclass
parser.print_help()
expected += """
usage: flag.py [-h] [--num_layers int] [--num_units int] [--optimizer str]
               [--learning_rate float] [--train bool]

optional arguments:
  -h, --help            show this help message and exit

HParams ['hparams']:
  Set of options for the training of a Model.

  --num_layers int      (default: 4)
  --num_units int       (default: 64)
  --optimizer str       (default: ADAM)
  --learning_rate float
                        (default: 0.001)
  --train bool, --no-train bool
                        (default: True)
"""
