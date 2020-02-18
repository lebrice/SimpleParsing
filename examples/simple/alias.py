from dataclasses import dataclass
from simple_parsing import ArgumentParser, choice, field


@dataclass
class HParams:
    """ Set of options for the training of a Model. """
    num_layers: int = field(4,  alias="-n")
    num_units:  int = field(64, alias="-u")
    optimizer:  str = field("ADAM", alias=["-o", "--opt"])
    learning_rate: float = field(0.001, alias="-lr")

parser = ArgumentParser()
parser.add_arguments(HParams, dest="hparams")
args = parser.parse_args()

print(args.hparams)
expected = "HParams(num_layers=4, num_units=64, optimizer='ADAM', learning_rate=0.001)"

parser.print_help()
expected += """
usage: alias.py [-h] [-n int] [-u int] [-o str] [-lr float]

optional arguments:
  -h, --help            show this help message and exit

HParams ['hparams']:
   Set of options for the training of a Model. 

  -n int, --num_layers int
  -u int, --num_units int
  -o str, --opt str, --optimizer str
  -lr float, --learning_rate float
"""