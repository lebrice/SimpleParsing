from dataclasses import dataclass
from simple_parsing import ArgumentParser

@dataclass
class Options:
    """ Set of Options for this script. """
    experiment_name: str        # a required string parameter
    learning_rate: float = 1e-4 # An optional float parameter

parser = ArgumentParser()  
parser.add_arguments(Options, dest="options")
args = parser.parse_args()

options: Options = args.options # retrieve the parsed values
print(options)

# Some example runs:
"""
$ python examples/demo.py --help
usage: demo.py [-h] --experiment_name str [--learning_rate float]

optional arguments:
  -h, --help            show this help message and exit

Options ['options']:
  Set of Options for this script.

  --experiment_name str
                        a required string parameter (default: None)
  --learning_rate float
                        An optional float parameter (default: 0.0001)

$ python examples/demo.py --experiment_name "bob"
Options(experiment_name='bob', learning_rate=0.0001)

$ python examples/demo.py
usage: demo.py [-h] --experiment_name str [--learning_rate float]
demo.py: error: the following arguments are required: --experiment_name

$ python examples/demo.py --experiment_name "bob" --learning_rate 1.23
Options(experiment_name='bob', learning_rate=1.23)





"""