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
parser.add_arguments(HParams, dest="hparams")


args = parser.parse_args()


print(args.hparams)
expected = """
HParams(num_layers=4, num_units=64, optimizer='ADAM', learning_rate=0.001)
"""


parser.print_help()
expected += """
usage: basic.py [-h] [--num_layers int] [--num_units int] [--optimizer str]
                [--learning_rate float]

optional arguments:
  -h, --help            show this help message and exit

HParams ['hparams']:
   Set of options for the training of a Model.

  --num_layers int      (default: 4)
  --num_units int       (default: 64)
  --optimizer str       (default: ADAM)
  --learning_rate float
                        (default: 0.001)
"""


print(parser.equivalent_argparse_code())
expected += """
parser = ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

group = parser.add_argument_group(title="HParams ['hparams']", description="Set of options for the training of a Model.")
group.add_argument(*['--num_layers'], **{'type': int, 'required': False, 'dest': 'hparams.num_layers', 'default': 4, 'help': ' '})
group.add_argument(*['--num_units'], **{'type': int, 'required': False, 'dest': 'hparams.num_units', 'default': 64, 'help': ' '})
group.add_argument(*['--optimizer'], **{'type': str, 'required': False, 'dest': 'hparams.optimizer', 'default': 'ADAM', 'help': ' '})
group.add_argument(*['--learning_rate'], **{'type': float, 'required': False, 'dest': 'hparams.learning_rate', 'default': 0.001, 'help': ' '})

args = parser.parse_args()
print(args)
"""
