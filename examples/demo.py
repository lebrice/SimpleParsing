"""examples/demo.py"""
import argparse
from dataclasses import dataclass

import simple_parsing

assert issubclass(simple_parsing.ArgumentParser, argparse.ArgumentParser)

parser = simple_parsing.ArgumentParser()

@dataclass
class Options:
    """ Group of command-line arguments for this script """
    log_dir: str                # a required string parameter
    learning_rate: float = 1e-4 # An optional float parameter

# you can add arguments as you usual would
parser.add_argument("--foo", dest="foo", type=int, default=123)

# or let the parser create the arguments for you
parser.add_arguments(Options, dest="options")

args = parser.parse_args()

foo: int = args.foo             # get the parsed 'foo' value
options: Options = args.options # get the parsed Options instance  
print("foo:", foo)
print("options:", options)

# Some example runs:
"""
$ python examples/demo.py --log_dir "logs"
foo: 123
options: Options(log_dir='logs', learning_rate=0.0001)

$ python examples/demo.py --help
usage: demo.py [-h] [--foo int] --log_dir str [--learning_rate float]

optional arguments:
  -h, --help            show this help message and exit
  --foo int

Options ['options']:
  Group of command-line arguments for this script

  --log_dir str         a required string parameter (default: None)
  --learning_rate float
                        An optional float parameter (default: 0.0001)
"""
