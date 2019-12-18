""" (examples/basic_example.py)
An example script without simple_parsing.
"""
from dataclasses import dataclass, asdict
# To start, simply replace this line:
## from argparse import ArgumentParser
from simple_parsing import ArgumentParser
# this ArgumentParser is simply a subclass of `argparse`'s ArgumentParser, so
# at first, nothing will change about how your script is executed.

@dataclass
class Options:
    """ A class which groups related parameters to be set via the Command line."""
    # Some required int parameter
    # (this comment will be used as the help text for the argument)
    some_required_int: int
    # An optional float parameter
    some_float: float = 1.23
    # The name of some important experiment
    name: str = "default"
    # an optional string parameter   
    log_dir: str = "/logs"
    # Wether or not to do something
    flag: bool = False

parser = ArgumentParser()
# adding argument the usual way still works just fine:
parser.add_argument("--batch_size",
  default=32,
  type=int,
  help="some help string for this argument",
)
# But why do that, when you could be doing this!
parser.add_arguments(Options, dest="options")

args = parser.parse_args()
print(vars(args))
"""$ python examples/basic_example.py --help
usage: basic_example.py [-h] [--batch_size int] --some_required_int int
                        [--some_float float] [--name str] [--log_dir str]
                        [--flag [str2bool]]

optional arguments:
  -h, --help            show this help message and exit
  --batch_size int      some help string for this argument (default: 32)

Options ['options']:
  A class which groups related parameters to be set via the Command line.

  --some_required_int int
                        Some required int parameter (this comment will be used
                        as the help text for the argument) (default: None)
  --some_float float    An optional float parameter (default: 1.23)
  --name str            The name of some important experiment (default:
                        default)
  --log_dir str         an optional string parameter (default: /logs)
  --flag [str2bool]     Wether or not to do something (default: False)
"""

batch_size: int = args.batch_size
options: Options = args.options
# The passed argument values have been set in the Options object,
# so you can use it do to whatever you like from here!

# for example, convert it to a dictionary and save it to a file:
import json # you could also use yaml, or whatever format you like
with open("options.json", "w") as f:
    options_dict = asdict(options)
    json.dump(options_dict, f, indent=1)

# or read the Options from a file:
with open("options.json", "r") as f:
    options_dict_ = json.load(f)
    options_ = Options(**options_dict_)

# and the values remain intact:
# (Note how using @dataclass above has given us the equality method for free!)
assert options == options_