from dataclasses import dataclass
from simple_parsing import ArgumentParser


@dataclass
class HParams:
    """ Set of options for the training of a Model."""
    num_layers: int = 4
    num_units:  int = 64
    optimizer:  str = "ADAM"
    learning_rate: float = 0.001

parser = ArgumentParser()
parser.add_arguments(HParams, dest="hparams")
args = parser.parse_args()

print(args.hparams)
expected = """
HParams(num_layers=4, num_units=64, optimizer='ADAM', learning_rate=0.001)
"""

parser.print_help()
expected += """
usage: basic.py [-h] [--num_layers int] [--num_units int]
                    [--optimizer str] [--learning_rate float]

optional arguments:
  -h, --help            show this help message and exit

HParams ['hparams']:
  Set of options for the training of a Model.

  --num_layers int
  --num_units int
  --optimizer str
  --learning_rate float
"""