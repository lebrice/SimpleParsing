from dataclasses import dataclass

from simple_parsing import ArgumentParser, field
from simple_parsing.wrappers.field_wrapper import ArgumentGenerationMode


@dataclass
class HParams:
    """Set of options for the training of a Model."""

    num_layers: int = field(4, alias="-n")
    num_units: int = field(64, alias="-u")
    optimizer: str = field("ADAM", alias=["-o", "--opt"])
    learning_rate: float = field(0.001, alias="-lr")


parser = ArgumentParser()
parser.add_arguments(HParams, dest="hparams")
args = parser.parse_args()

print(args.hparams)
expected = """
HParams(num_layers=4, num_units=64, optimizer='ADAM', learning_rate=0.001)
"""

parser.print_help()
expected += """
usage: option_strings.py [-h] [-n int] [-u int] [-o str] [-lr float]

optional arguments:
  -h, --help            show this help message and exit

HParams ['hparams']:
   Set of options for the training of a Model.

  -n int, --num_layers int
                        (default: 4)
  -u int, --num_units int
                        (default: 64)
  -o str, --opt str, --optimizer str
                        (default: ADAM)
  -lr float, --learning_rate float
                        (default: 0.001)
"""

# Now if we wanted to also be able to set the arguments using their full paths:
parser = ArgumentParser(argument_generation_mode=ArgumentGenerationMode.BOTH)
parser.add_arguments(HParams, dest="hparams")
parser.print_help()
expected += """
usage: option_strings.py [-h] [-n int] [-u int] [-o str] [-lr float]

optional arguments:
  -h, --help            show this help message and exit

HParams ['hparams']:
   Set of options for the training of a Model.

  -n int, --num_layers int, --hparams.num_layers int
                        (default: 4)
  -u int, --num_units int, --hparams.num_units int
                        (default: 64)
  -o str, --opt str, --optimizer str, --hparams.optimizer str
                        (default: ADAM)
  -lr float, --learning_rate float, --hparams.learning_rate float
                        (default: 0.001)
"""
