from dataclasses import dataclass
from simple_parsing import ArgumentParser


@dataclass
class Method:
    """ Set of options for the training of a Model."""
    num_layers: int = 4
    num_units:  int = 64
    optimizer:  str = "ADAM"
    learning_rate: float = 0.001


@dataclass
class MAML(Method):
    """Overwrites some of the default values and adds new arguments/attributes.
    """
    num_layers: int = 6
    num_units:  int = 128

    # method
    name: str = "MAML"



parser = ArgumentParser()
parser.add_arguments(MAML, dest="hparams")
args = parser.parse_args()


print(args.hparams)
expected = """
MAML(num_layers=6, num_units=128, optimizer='ADAM', learning_rate=0.001, name='MAML')
"""



parser.print_help()
expected += """
usage: inheritance.py [-h] [--num_layers int] [--num_units int]
                      [--optimizer str] [--learning_rate float] [--name str]

optional arguments:
  -h, --help            show this help message and exit

MAML ['hparams']:
  Overwrites some of the default values and adds new arguments/attributes.
      

  --num_layers int
  --num_units int
  --optimizer str
  --learning_rate float
  --name str            method (default: MAML)
"""


print(parser.equivalent_argparse_code())
expected += """
parser = ArgumentParser()

group = parser.add_argument_group(title="MAML ['hparams']", description="Overwrites some of the default values and adds new arguments/attributes.")
group.add_argument(*['--num_layers'], **{'type': int, 'help': None, 'required': False, 'dest': 'hparams.num_layers', 'default': 6})
group.add_argument(*['--num_units'], **{'type': int, 'help': None, 'required': False, 'dest': 'hparams.num_units', 'default': 128})
group.add_argument(*['--optimizer'], **{'type': str, 'help': None, 'required': False, 'dest': 'hparams.optimizer', 'default': 'ADAM'})
group.add_argument(*['--learning_rate'], **{'type': float, 'help': None, 'required': False, 'dest': 'hparams.learning_rate', 'default': 0.001})
group.add_argument(*['--name'], **{'type': str, 'help': 'method', 'required': False, 'dest': 'hparams.name', 'default': 'MAML'})

args = parser.parse_args()
print(args)
"""