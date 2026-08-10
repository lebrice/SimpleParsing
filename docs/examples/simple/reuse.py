"""Modular and reusable! With SimpleParsing, you can easily add similar groups of command-line
arguments by simply reusing the dataclasses you define! There is no longer need for any copy-
pasting of blocks, or adding prefixes everywhere by hand.

Instead, the ArgumentParser detects when more than one instance of the same `@dataclass` needs to
be parsed, and automatically adds the relevant prefixes to the arguments for you.
"""

from dataclasses import dataclass

from simple_parsing import ArgumentParser


@dataclass
class HParams:
    """Set of options for the training of a Model."""

    num_layers: int = 4
    num_units: int = 64
    optimizer: str = "ADAM"
    learning_rate: float = 0.001


parser = ArgumentParser()
parser.add_arguments(HParams, dest="train")
parser.add_arguments(HParams, dest="valid")
args = parser.parse_args()

print(args.train)
print(args.valid)
expected = """
HParams(num_layers=4, num_units=64, optimizer='ADAM', learning_rate=0.001)
HParams(num_layers=4, num_units=64, optimizer='ADAM', learning_rate=0.001)
"""

parser.print_help()
expected += """
usage: reuse.py [-h] [--train.num_layers int] [--train.num_units int]
                [--train.optimizer str] [--train.learning_rate float]
                [--valid.num_layers int] [--valid.num_units int]
                [--valid.optimizer str] [--valid.learning_rate float]

optional arguments:
  -h, --help            show this help message and exit

HParams ['train']:
   Set of options for the training of a Model.

  --train.num_layers int
                        (default: 4)
  --train.num_units int
                        (default: 64)
  --train.optimizer str
                        (default: ADAM)
  --train.learning_rate float
                        (default: 0.001)

HParams ['valid']:
   Set of options for the training of a Model.

  --valid.num_layers int
                        (default: 4)
  --valid.num_units int
                        (default: 64)
  --valid.optimizer str
                        (default: ADAM)
  --valid.learning_rate float
                        (default: 0.001)
"""
